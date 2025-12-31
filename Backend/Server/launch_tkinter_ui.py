"""
Launcher script for Tkinter UI
Checks if backend server is running and launches the UI
"""
import subprocess
import sys
import time
import os

# Check for requests library
try:
    import requests
except ImportError:
    print("ERROR: 'requests' library is required.")
    print("Please install it using: pip install requests")
    sys.exit(1)

API_BASE_URL = "http://localhost:8000"

def check_backend():
    """Check if backend server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_backend():
    """Try to start the backend server"""
    print("Attempting to start backend server...")
    try:
        # Try to start server.py
        if os.path.exists("server.py"):
            print("Starting server.py...")
            subprocess.Popen([sys.executable, "server.py"], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
            # Wait a bit for server to start
            for i in range(10):
                time.sleep(1)
                if check_backend():
                    print("✓ Backend server started successfully!")
                    return True
            print("⚠ Backend server may still be starting. Please wait...")
            return False
        else:
            print("✗ server.py not found in current directory.")
            return False
    except Exception as e:
        print(f"✗ Failed to start backend: {e}")
        return False

def main():
    print("=" * 60)
    print("Secure Wipe - Tkinter UI Launcher")
    print("=" * 60)
    print()
    
    # Check if backend is running
    print("Checking backend server connection...")
    if check_backend():
        print("✓ Backend server is running!")
    else:
        print("✗ Backend server is not running.")
        print()
        response = input("Would you like to start it now? (y/n): ").strip().lower()
        if response == 'y':
            if not start_backend():
                print()
                print("Please start the backend server manually:")
                print("  python server.py")
                print()
                print("Then run this launcher again.")
                sys.exit(1)
        else:
            print()
            print("Please start the backend server first:")
            print("  python server.py")
            print()
            print("Then run this launcher again.")
            sys.exit(1)
    
    print()
    print("Launching Tkinter UI...")
    print()
    
    # Import and run the UI
    try:
        from tkinter_ui import SecureWipeApp
        import tkinter as tk
        
        root = tk.Tk()
        app = SecureWipeApp(root)
        root.mainloop()
    except ImportError as e:
        print(f"✗ Failed to import tkinter_ui: {e}")
        print("Make sure tkinter_ui.py is in the same directory.")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error launching UI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

