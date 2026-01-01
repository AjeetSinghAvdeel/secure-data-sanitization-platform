import os
import shutil
import platform
import psutil
import subprocess
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import Union
import secrets
from datetime import datetime
import uuid
import json
import tempfile

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- Load environment variables ---
from dotenv import load_dotenv
# Load environment files: prefer .env.local then fallback to .env
load_dotenv('.env.local', override=False)
load_dotenv(override=False)

# --- Import auth utils ---
from auth_utils import verify_firebase_token, verify_optional_token

# --- Firebase ---
import firebase_admin
from firebase_admin import credentials, firestore

db = None
try:
    if not firebase_admin._apps:
        firebase_key_json = os.getenv("FIREBASE_KEY_JSON")
        
        if firebase_key_json:
            # Load from environment variable (JSON string)
            try:
                key_dict = json.loads(firebase_key_json)
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
                db = firestore.client()
                print("[OK] Firebase initialized successfully from FIREBASE_KEY_JSON env var")
            except Exception as e:
                print(f"[WARNING] Failed to parse FIREBASE_KEY_JSON: {e}")
                db = None
        elif os.path.exists("firebase_key.json"):
            # Fallback: load from local file (for development)
            cred = credentials.Certificate("firebase_key.json")
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("[OK] Firebase initialized successfully from firebase_key.json")
        else:
            print("[WARNING] FIREBASE_KEY_JSON env var not set and firebase_key.json not found.")
            print("  Firebase features will be disabled. Set FIREBASE_KEY_JSON env var to enable.")
except Exception as e:
    print(f"[WARNING] Firebase initialization failed: {e}")
    print("  Certificates will not be saved to Firebase, but local operations will work.")
    db = None

app = FastAPI(
    title="Secure Wipe API",
    description="API for secure data wiping and certificate management",
    version="1.0.0"
)

# Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Secure Wipe API Server",
        "status": "running",
        "docs": "/docs",
        "version": "1.0.0"
    }

# ---------- Models ----------
class WipeRequest(BaseModel):
    mountpoint: str
    passes: int = 1   # default single-pass overwrite

class SettingsUpdate(BaseModel):
    wipeMethod: str = "3-pass"
    generateCerts: bool = True
    includeQRCode: bool = True
    compliance: str = "NIST SP 800-88"
    tamperDetection: bool = True

class VerifyWipeRequest(BaseModel):
    file_path: str
    original_hash: str = None


# ---------- Settings (new) ----------
SETTINGS_FILE = "settings.json"
default_settings = {
    "wipeMethod": "3-pass",
    "generateCerts": True,
    "includeQRCode": True,
    "compliance": "NIST SP 800-88",
    "tamperDetection": True,
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return default_settings

def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f)

@app.get("/api/settings")
def get_settings():
    return load_settings()

@app.post("/api/settings")
def update_settings(new_settings: Union[SettingsUpdate, dict], user: dict = Depends(verify_firebase_token)):
    # Handle both dict and Pydantic model
    if isinstance(new_settings, dict):
        settings_dict = new_settings
    else:
        settings_dict = new_settings.model_dump()
    save_settings(settings_dict)
    return {"status": "success", "settings": settings_dict}


# ---------- Health Endpoint (new) ----------
@app.get("/api/health")
def get_health():
    # Get disk usage - use appropriate root path for OS
    system = platform.system()
    if system == "Windows":
        disk_path = "C:\\"
    else:
        disk_path = "/"
    
    try:
        disk_usage = psutil.disk_usage(disk_path).percent
    except:
        disk_usage = 0
    
    return {
        "cpu": psutil.cpu_percent(interval=0.5),
        "memory": psutil.virtual_memory().percent,
        "disk": disk_usage,
        "aiModelsActive": True,
        "connected": True
    }


# ---------- Risk Analysis ----------
HIGH_RISK_EXT = {".docx", ".doc", ".pdf", ".xls", ".xlsx", ".ppt", ".pptx", ".db", ".key", ".pem"}
MEDIUM_RISK_EXT = {".jpg", ".jpeg", ".png", ".gif", ".mp4", ".avi", ".zip", ".rar"}
LOW_RISK_EXT = {".txt", ".log", ".tmp"}

def analyze_device(mountpoint, max_files=200):
    risky_files = []
    score = 0
    count = 0
    for root, dirs, files in os.walk(mountpoint):
        for name in files:
            if count >= max_files:
                break
            ext = os.path.splitext(name)[1].lower()
            if ext in HIGH_RISK_EXT:
                score += 5
                level = "high"
            elif ext in MEDIUM_RISK_EXT:
                score += 3
                level = "medium"
            elif ext in LOW_RISK_EXT:
                score += 1
                level = "low"
            else:
                level = "unknown"
            risky_files.append({"file": os.path.join(root, name), "risk": level})
            count += 1
    risk_score = min(100, score)
    return {"risk_score": risk_score, "files": risky_files[:20]}


# ---------- Health Check ----------
def get_device_health(device_path: str) -> int:
    system = platform.system()
    try:
        if system in ["Darwin", "Linux"]:
            result = subprocess.run(
                ["smartctl", "-H", device_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if "PASSED" in result.stdout:
                return 100
            elif "FAILED" in result.stdout:
                return 10
            else:
                return 70
        elif system == "Windows":
            result = subprocess.run(
                ["wmic", "diskdrive", "get", "status"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if "OK" in result.stdout:
                return 100
            elif "Pred Fail" in result.stdout:
                return 20
            else:
                return 70
    except Exception as e:
        print(f"SMART health check failed: {e}")
    return 80


# ---------- Device Detection ----------
def _get_removable_devices():
    devices = []
    system = platform.system()
    if system == "Windows":
        for part in psutil.disk_partitions(all=False):
            if "removable" in part.opts.lower():
                usage = shutil.disk_usage(part.mountpoint)
                analysis = analyze_device(part.mountpoint)
                health = get_device_health(part.device)
                devices.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "total": usage.total,
                    "free": usage.free,
                    "analysis": analysis,
                    "health": health
                })
    elif system == "Darwin":  # macOS
        base = "/Volumes"
        if os.path.exists(base):
            for entry in os.listdir(base):
                mp = os.path.join(base, entry)
                if entry.startswith("."):
                    continue
                if os.path.ismount(mp):
                    usage = shutil.disk_usage(mp)
                    analysis = analyze_device(mp)
                    health = get_device_health("/dev/disk2")
                    devices.append({
                        "device": entry,
                        "mountpoint": mp,
                        "total": usage.total,
                        "free": usage.free,
                        "analysis": analysis,
                        "health": health
                    })
    elif system == "Linux":
        base = "/media"
        if os.path.exists(base):
            for user in os.listdir(base):
                user_dir = os.path.join(base, user)
                if os.path.isdir(user_dir):
                    for entry in os.listdir(user_dir):
                        mp = os.path.join(user_dir, entry)
                        if os.path.ismount(mp):
                            usage = shutil.disk_usage(mp)
                            analysis = analyze_device(mp)
                            health = get_device_health("/dev/sdb")
                            devices.append({
                                "device": entry,
                                "mountpoint": mp,
                                "total": usage.total,
                                "free": usage.free,
                                "analysis": analysis,
                                "health": health
                            })
    return devices


# ---------- Laptop/System Storage ----------
def analyze_storage(path: str):
    usage = psutil.disk_usage(path)
    free_percent = usage.free / usage.total * 100
    risk_score = 100 - int(free_percent)
    health = int(free_percent)
    return {
        "mountpoint": path,
        "total": usage.total,
        "free": usage.free,
        "health": health,
        "analysis": {
            "risk_score": risk_score,
            "files": []
        }
    }

@app.get("/devices")
def list_devices():
    return {"devices": _get_removable_devices()}

@app.get("/system-analysis")
def system_analysis():
    # Use appropriate root path for OS
    system = platform.system()
    if system == "Windows":
        root_path = "C:\\"
    else:
        root_path = "/"
    return {"system": analyze_storage(root_path)}


# ---------- Certificates (Firestore) ----------
CERT_PDF_DIR = "cert_pdfs"
os.makedirs(CERT_PDF_DIR, exist_ok=True)

def load_certificates():
    if db is None:
        return []
    try:
        docs = db.collection("certificates").stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"Error loading certificates from Firebase: {e}")
        return []

def save_certificate(cert):
    if db is None:
        print("Warning: Cannot save certificate - Firebase not initialized")
        return
    try:
        db.collection("certificates").document(cert["id"]).set(cert)
    except Exception as e:
        print(f"Error saving certificate to Firebase: {e}")

def generate_pdf(cert):
    pdf_path = os.path.join(CERT_PDF_DIR, f"{cert['id']}.pdf")
    if os.path.exists(pdf_path):
        return pdf_path
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 100, "Data Wipe Certificate")
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 160, f"Certificate ID: {cert['id']}")
    c.drawString(100, height - 180, f"Device: {cert['device']}")
    c.drawString(100, height - 200, f"Method: {cert['method']}")
    c.drawString(100, height - 220, f"Date: {cert['date']}")
    c.drawString(100, height - 240, f"Status: {cert['status']}")
    c.showPage()
    c.save()
    return pdf_path

@app.get("/api/certificates")
def get_certificates():
    return load_certificates()

@app.get("/api/certificates/{cert_id}")
def get_certificate(cert_id: str):
    if db is None:
        raise HTTPException(status_code=503, detail="Firebase not initialized")
    try:
        doc = db.collection("certificates").document(cert_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Certificate not found")
        return doc.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/certificates/download/{cert_id}")
def download_certificate(cert_id: str, user: dict = Depends(verify_firebase_token)):
    if db is None:
        raise HTTPException(status_code=503, detail="Firebase not initialized")
    try:
        doc = db.collection("certificates").document(cert_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Certificate not found")
        pdf_path = generate_pdf(doc.to_dict())
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"certificate_{cert_id}.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Wipe USB ----------
@app.post("/wipe-usb")
def wipe_usb(req: WipeRequest, user: dict = Depends(verify_firebase_token)):
    mp = req.mountpoint
    passes = max(1, req.passes)
    if not os.path.exists(mp):
        raise HTTPException(status_code=404, detail="Mountpoint not found")
    
    # Store file hashes before wipe for verification
    file_hashes_before = {}
    try:
        for root, dirs, files in os.walk(mp):
            for name in files:
                file_path = os.path.join(root, name)
                try:
                    # Calculate hash before wipe
                    from verify_wipe import calculate_file_hash
                    file_hashes_before[file_path] = calculate_file_hash(file_path)
                except:
                    pass
        
        # Perform wipe
        files_wiped = 0
        for root, dirs, files in os.walk(mp):
            for name in files:
                file_path = os.path.join(root, name)
                try:
                    length = os.path.getsize(file_path)
                    with open(file_path, "r+b") as f:
                        for _ in range(passes):
                            f.seek(0)
                            f.write(secrets.token_bytes(length))
                            f.flush()
                            os.fsync(f.fileno())
                    os.remove(file_path)
                    files_wiped += 1
                except Exception as e:
                    print(f"Error wiping {file_path}: {e}")
        
        cert_id = str(uuid.uuid4())[:8]
        cert = {
            "id": cert_id,
            "device": mp,
            "method": f"Secure Wipe ({passes}-pass overwrite)",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "VALID",
            "files_wiped": files_wiped,
            "verification_data": {
                "files_hashed_before": len(file_hashes_before),
                "passes": passes
            }
        }
        save_certificate(cert)
        auto_register_certificate(cert)
        return {
            "status": "success", 
            "message": f"Data wiped on {mp}", 
            "certificate": cert,
            "files_wiped": files_wiped
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Compliance Endpoint ----------
@app.get("/compliance")
def compliance_check():
    # Use appropriate root path for OS
    system = platform.system()
    if system == "Windows":
        root_path = "C:\\"
    else:
        root_path = "/"
    
    nist_score = 100 if load_certificates() else 0
    system_drive = analyze_storage(root_path)
    gdpr_score = 100 if nist_score == 100 else (50 if system_drive["analysis"]["risk_score"] > 20 else 80)
    certs = load_certificates()
    dod_score = 0
    for c in certs:
        if "3-pass" in c["method"] or "multi-pass" in c["method"]:
            dod_score = 100
            break
    if dod_score == 0 and nist_score == 100:
        dod_score = 50
    overall = int((nist_score + gdpr_score + dod_score) / 3)
    return {"nist_sp_800_88": nist_score, "gdpr_article_17": gdpr_score, "dod_5220_22m": dod_score, "overall": overall}


# ---------- Tamper Check ----------
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

PRIVATE_KEY_FILE = "private_key.pem"
PUBLIC_KEY_FILE = "public_key.pem"

def generate_keys():
    if not os.path.exists(PRIVATE_KEY_FILE):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        with open(PRIVATE_KEY_FILE, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        with open(PUBLIC_KEY_FILE, "wb") as f:
            f.write(private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

def load_private_key():
    with open(PRIVATE_KEY_FILE, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def load_public_key():
    with open(PUBLIC_KEY_FILE, "rb") as f:
        return serialization.load_pem_public_key(f.read())

def compute_hash(data: bytes) -> str:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize().hex()

def auto_register_certificate(cert):
    if db is None:
        print("Warning: Cannot register certificate in tamper DB - Firebase not initialized")
        return
    try:
        generate_keys()
        private_key = load_private_key()
        cert_bytes = json.dumps(cert, sort_keys=True).encode()
        file_hash = compute_hash(cert_bytes)
        signature = private_key.sign(cert_bytes, padding.PKCS1v15(), hashes.SHA256())
        db.collection("tamper_db").document(cert["id"]).set({
            "hash": file_hash,
            "signature": signature.hex(),
            "device": cert["device"],
            "method": cert["method"],
            "date": cert["date"],
            "status": cert["status"]
        })
    except Exception as e:
        print(f"Error registering certificate in tamper DB: {e}")

@app.get("/tamper/verify/{cert_id}")
def verify_certificate(cert_id: str):
    if db is None:
        return {"status": "firebase_not_initialized", "id": cert_id, "message": "Firebase not available"}
    try:
        public_key = load_public_key()
        doc = db.collection("tamper_db").document(cert_id).get()
        if not doc.exists:
            return {"status": "not_registered", "id": cert_id}
        data = doc.to_dict()
        cert = {
            "id": cert_id,
            "device": data["device"],
            "method": data["method"],
            "date": data["date"],
            "status": data["status"]
        }
        cert_bytes = json.dumps(cert, sort_keys=True).encode()
        file_hash = compute_hash(cert_bytes)
        signature = bytes.fromhex(data["signature"])
        try:
            public_key.verify(signature, cert_bytes, padding.PKCS1v15(), hashes.SHA256())
            tampered = (data["hash"] != file_hash)
            return {"status": "verified" if not tampered else "tampered",
                    "id": cert_id, "expected_hash": data["hash"], "current_hash": file_hash}
        except Exception:
            return {"status": "invalid_signature", "id": cert_id}
    except Exception as e:
        return {"status": "error", "id": cert_id, "message": str(e)}

# ---------- Wipe Verification ----------
@app.post("/api/verify-wipe")
def verify_wipe_endpoint(req: VerifyWipeRequest, user: dict = Depends(verify_firebase_token)):
    """Verify that a file has been properly wiped"""
    try:
        from verify_wipe import verify_wipe_completeness
        result = verify_wipe_completeness(req.file_path, req.original_hash)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/verify-directory")
def verify_directory_wipe_endpoint(directory_path: str, user: dict = Depends(verify_firebase_token)):
    """Verify that all files in a directory have been wiped"""
    try:
        from verify_wipe import verify_directory_wipe
        result = verify_directory_wipe(directory_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system-status")
def system_status():
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory().percent
        return {
            "cpu": cpu,
            "memory": memory,
            "ai_models": True,   
            "connected": True   
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Custom 404 handler
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={
                "detail": f"Endpoint not found: {request.method} {request.url.path}",
                "message": "The requested endpoint does not exist.",
                "available_endpoints": [
                    "GET /",
                    "GET /api/health",
                    "GET /api/settings",
                    "POST /api/settings",
                    "GET /devices",
                    "GET /system-analysis",
                    "GET /api/certificates",
                    "GET /api/certificates/{cert_id}",
                    "GET /api/certificates/download/{cert_id}",
                    "POST /wipe-usb",
                    "GET /compliance",
                    "GET /tamper/verify/{cert_id}",
                    "GET /system-status",
                    "GET /docs (Swagger UI)",
                    "GET /redoc (ReDoc)"
                ],
                "hint": "Check the API documentation at /docs for all available endpoints"
            }
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Request validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "path": str(request.url.path)
        }
    )


# ---------- Run Server ----------
if __name__ == "__main__":
    import uvicorn
    print("Starting Secure Wipe API Server...")
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")
        print("\nMake sure uvicorn is installed: pip install uvicorn")
