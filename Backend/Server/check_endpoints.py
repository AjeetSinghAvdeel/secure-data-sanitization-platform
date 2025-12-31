"""
Script to check if all endpoints are accessible
"""
import requests
import json

API_BASE = "http://localhost:8000"

endpoints = [
    ("GET", "/"),
    ("GET", "/api/health"),
    ("GET", "/api/settings"),
    ("GET", "/devices"),
    ("GET", "/system-analysis"),
    ("GET", "/api/certificates"),
    ("GET", "/compliance"),
    ("GET", "/system-status"),
]

print("Checking API endpoints...")
print("=" * 60)

for method, endpoint in endpoints:
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, timeout=5)
        
        status = response.status_code
        if status == 200:
            print(f"[OK] {method} {endpoint} - Status: {status}")
        elif status == 404:
            print(f"[NOT FOUND] {method} {endpoint} - Status: {status}")
            try:
                error_data = response.json()
                print(f"  Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"  Error: {response.text}")
        else:
            print(f"[WARNING] {method} {endpoint} - Status: {status}")
            try:
                error_data = response.json()
                print(f"  Response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"  Response: {response.text[:200]}")
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] {method} {endpoint} - Cannot connect to server")
        print("  Make sure the server is running: python server.py")
        break
    except Exception as e:
        print(f"[ERROR] {method} {endpoint} - {str(e)}")

print("=" * 60)
print("\nTo start the server, run: python server.py")

