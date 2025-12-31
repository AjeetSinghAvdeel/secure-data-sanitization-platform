"""
Quick test script to verify server.py can start without errors
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing server.py imports and initialization...")
print("=" * 60)

try:
    # Test imports
    print("1. Testing imports...")
    import server
    print("   [OK] All imports successful")
    
    # Check if app is created
    print("2. Checking FastAPI app...")
    if hasattr(server, 'app'):
        print("   [OK] FastAPI app created")
    else:
        print("   [ERROR] FastAPI app not found")
        sys.exit(1)
    
    # Check Firebase initialization
    print("3. Checking Firebase...")
    if server.db is None:
        print("   [WARNING] Firebase not initialized (this is OK if firebase_key.json is missing)")
    else:
        print("   [OK] Firebase initialized")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Server.py is ready to run!")
    print("\nTo start the server, run:")
    print("  python server.py")
    print("\nOr use uvicorn directly:")
    print("  uvicorn server:app --host 0.0.0.0 --port 8000")
    
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("\nMissing dependencies. Install with:")
    print("  pip install fastapi uvicorn psutil firebase-admin cryptography reportlab")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

