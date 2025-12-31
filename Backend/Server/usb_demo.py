import os
import io
import sys
import json
import time
import ctypes
import shutil
import random
import string
import platform
from typing import List, Dict, Any

from flask import Flask, request, jsonify, send_file
import psutil
from flask_cors import CORS

try:
    import pytsk3  # type: ignore
except Exception as e:  # pragma: no cover
    pytsk3 = None  # will handle at runtime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# -------- Utils --------

def is_admin() -> bool:
    try:
        if platform.system() == "Windows":
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        else:
            return os.geteuid() == 0
    except Exception:
        return False


def list_removable_devices() -> List[Dict[str, Any]]:
    devices = []
    for part in psutil.disk_partitions(all=False):
        opts = (part.opts or "").lower()
        try:
            if "removable" in opts or (platform.system() != "Windows" and "rw" in opts and part.device and "/dev/sd" in part.device):
                usage = shutil.disk_usage(part.mountpoint)
                devices.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total": usage.total,
                    "free": usage.free,
                })
        except Exception:
            pass
    return devices


# Map a mountpoint like E:\\ to a raw path suitable for pytsk3 (best-effort on Windows)

def get_raw_path(mount_or_device: str) -> str:
    if platform.system() == "Windows":
        # If given like 'E:\\' use \\.\E:
        drive = mount_or_device.strip().rstrip("\\/")
        if len(drive) == 2 and drive.endswith(":"):
            return f"\\\\.\\{drive}"
        if os.path.isdir(mount_or_device) and len(os.path.splitdrive(mount_or_device)[0]) == 2:
            d = os.path.splitdrive(mount_or_device)[0]
            return f"\\\\.\\{d}"
        # Otherwise assume raw path already
        return mount_or_device
    # Linux/macOS: assume device path is provided
    return mount_or_device


# -------- TSK Helpers --------

def tsk_open_image(raw_path: str):
    if pytsk3 is None:
        raise RuntimeError("pytsk3 not installed. Install with: pip install pytsk3")
    return pytsk3.Img_Info(raw_path)


def tsk_find_deleted(img) -> List[Dict[str, Any]]:
    """Traverse filesystem and list deleted (unallocated) files (best-effort)."""
    results: List[Dict[str, Any]] = []
    try:
        fs = pytsk3.FS_Info(img)
    except Exception as e:
        raise RuntimeError(f"Unable to open filesystem with TSK: {e}")

    def walk_dir(directory):
        for entry in directory:
            try:
                name = entry.info.name.name.decode(errors="ignore") if entry.info.name.name else ""
            except Exception:
                name = ""
            if name in (".", ".."):
                continue
            try:
                meta = entry.info.meta
            except Exception:
                meta = None
            try:
                path = entry.info.name.name.decode(errors="ignore")
            except Exception:
                path = ""
            full_path = f"/{path}" if path.startswith("/") else f"/{path}"
            try:
                if meta and meta.type == pytsk3.TSK_FS_META_TYPE_REG:
                    is_deleted = bool(meta.flags & pytsk3.TSK_FS_META_FLAG_UNALLOC)
                    if is_deleted:
                        results.append({
                            "name": name,
                            "path": full_path,
                            "inode": int(meta.addr),
                            "size": int(meta.size or 0),
                            "deleted": True,
                        })
                if entry.info.meta and entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
                    sub_dir = entry.as_directory()
                    walk_dir(sub_dir)
            except Exception:
                # ignore inaccessible entries
                pass

    root_dir = fs.open_dir(path="/")
    walk_dir(root_dir)
    return results


def tsk_recover_file(img, inode: int) -> bytes:
    fs = pytsk3.FS_Info(img)
    f = fs.open_meta(inode=inode)
    size = int(f.info.meta.size)
    chunks = []
    offset = 0
    CHUNK = 1024 * 1024
    while offset < size:
        to_read = min(CHUNK, size - offset)
        data = f.read_random(offset, to_read)
        if not data:
            break
        chunks.append(data)
        offset += len(data)
    return b"".join(chunks)


# -------- Routes --------

@app.get("/usb/devices")
def get_devices():
    return jsonify({"devices": list_removable_devices(), "admin": is_admin()})


@app.post("/usb/scan")
def usb_scan():
    data = request.get_json(silent=True) or {}
    device = data.get("device") or data.get("mountpoint")
    if not device:
        return jsonify({"error": "device or mountpoint required"}), 400
    raw = get_raw_path(device)
    try:
        img = tsk_open_image(raw)
        files = tsk_find_deleted(img)
        return jsonify({"count": len(files), "files": files[:200]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/usb/recover")
def usb_recover():
    data = request.get_json(silent=True) or {}
    device = data.get("device") or data.get("mountpoint")
    inode = data.get("inode")
    out_dir = data.get("output_dir") or os.path.join(os.getcwd(), "recovered")
    # Recovery is non-destructive; no admin/confirm required
    if not device or not inode:
        return jsonify({"error": "device and inode required"}), 400

    os.makedirs(out_dir, exist_ok=True)
    raw = get_raw_path(device)
    try:
        img = tsk_open_image(raw)
        blob = tsk_recover_file(img, int(inode))
        # Generate a safe filename
        fname = f"recovered_{inode}_{int(time.time())}.bin"
        out_path = os.path.join(out_dir, fname)
        with open(out_path, "wb") as f:
            f.write(blob)
        return jsonify({"status": "ok", "bytes": len(blob), "file": out_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/usb/recover_stream")
def usb_recover_stream():
    data = request.get_json(silent=True) or {}
    device = data.get("device") or data.get("mountpoint")
    inode = data.get("inode")
    filename = data.get("filename") or f"recovered_{inode}_{int(time.time())}.bin"
    if not device or not inode:
        return jsonify({"error": "device and inode required"}), 400
    raw = get_raw_path(device)
    try:
        img = tsk_open_image(raw)
        blob = tsk_recover_file(img, int(inode))
        bio = io.BytesIO(blob)
        bio.seek(0)
        return send_file(
            bio,
            as_attachment=True,
            download_name=filename,
            mimetype="application/octet-stream",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/usb/wipe")
def usb_wipe():
    data = request.get_json(silent=True) or {}
    mountpoint = data.get("mountpoint")
    method = (data.get("method") or "zeros").lower()  # zeros|random|dod
    confirm = bool(data.get("confirm"))

    if not confirm:
        return jsonify({"error": "confirm=true required for wipe"}), 400
    if not is_admin():
        return jsonify({"error": "admin privileges required"}), 403
    if not mountpoint or not os.path.isdir(mountpoint):
        return jsonify({"error": "valid mountpoint required"}), 400

    files_wiped = 0
    passes = 1
    if method == "dod":
        passes = 3
    elif method == "random":
        passes = 1
    elif method == "zeros":
        passes = 1

    for root, _, files in os.walk(mountpoint):
        for name in files:
            fpath = os.path.join(root, name)
            try:
                length = os.path.getsize(fpath)
                with open(fpath, "r+b", buffering=0) as f:
                    for p in range(passes):
                        f.seek(0)
                        if method == "zeros":
                            chunk = b"\x00" * 1024 * 1024
                            written = 0
                            while written < length:
                                f.write(chunk[: min(1024 * 1024, length - written)])
                                written += min(1024 * 1024, length - written)
                        elif method in ("random", "dod"):
                            written = 0
                            while written < length:
                                chunk = os.urandom(min(1024 * 1024, length - written))
                                f.write(chunk)
                                written += len(chunk)
                        f.flush()
                        os.fsync(f.fileno())
                os.remove(fpath)
                files_wiped += 1
            except Exception:
                pass
    return jsonify({"status": "ok", "method": method, "passes": passes, "files_wiped": files_wiped})


@app.get("/")
def root():
    return jsonify({
        "service": "USB Demo Flask Agent",
        "endpoints": [
            "GET /usb/devices",
            "POST /usb/scan",
            "POST /usb/recover",
            "POST /usb/wipe",
        ],
        "requires_admin": True,
    })


if __name__ == "__main__":
    port = int(os.environ.get("USB_DEMO_PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=True)
