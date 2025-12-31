# Tkinter Desktop UI - Secure Wipe Application

This is a comprehensive desktop application built with Tkinter that replicates all the functionality of the web frontend. It connects to the same FastAPI backend, ensuring all your data is preserved.

## Features

### 1. **Dashboard Tab**
- Real-time system health monitoring (CPU, Memory, Disk usage)
- Quick actions for common tasks
- Activity log for all operations

### 2. **Devices Tab**
- Automatic device scanning and detection
- Device details with risk analysis
- Secure wipe functionality with configurable passes
- Real-time device health monitoring

### 3. **Certificates Tab**
- View all certificates from Firebase
- Download certificate PDFs
- View detailed certificate information
- Certificate status tracking

### 4. **Settings Tab**
- Configure wipe methods (1-pass, 3-pass, 7-pass)
- Enable/disable certificate generation
- QR code inclusion settings
- Compliance standard selection
- Tamper detection toggle

### 5. **Compliance Tab**
- NIST SP 800-88 compliance score
- GDPR Article 17 compliance score
- DoD 5220.22-M compliance score
- Overall compliance percentage

### 6. **Tamper Detection Tab**
- Verify certificate integrity
- Detect tampering attempts
- View verification results and hash comparisons

## Installation

### Prerequisites
```bash
pip install requests
```

The following are already required for the backend:
- `fastapi`
- `psutil`
- `firebase-admin`
- `cryptography`
- `reportlab`

## Usage

### Option 1: Using the Launcher (Recommended)
```bash
python launch_tkinter_ui.py
```

The launcher will:
- Check if the backend server is running
- Offer to start it automatically if needed
- Launch the Tkinter UI

### Option 2: Manual Launch
1. First, start the backend server:
```bash
python server.py
```

2. Then, in another terminal, run:
```bash
python tkinter_ui.py
```

## Backend Connection

The Tkinter UI connects to the FastAPI backend running on:
- **URL**: `http://localhost:8000`
- **Default Port**: 8000

If your backend runs on a different port, edit `API_BASE_URL` in `tkinter_ui.py`:
```python
API_BASE_URL = "http://localhost:YOUR_PORT"
```

## Data Preservation

✅ **All data is preserved** because:
- The UI uses the same API endpoints as the web frontend
- Certificates are stored in Firebase (same database)
- Settings are saved to the same `settings.json` file
- All wipe operations create certificates in the same system

## Features Comparison

| Feature | Web Frontend | Tkinter UI |
|---------|-------------|------------|
| Device Scanning | ✅ | ✅ |
| Secure Wipe | ✅ | ✅ |
| Certificate Management | ✅ | ✅ |
| Settings | ✅ | ✅ |
| Compliance Dashboard | ✅ | ✅ |
| Tamper Detection | ✅ | ✅ |
| System Health | ✅ | ✅ |
| Risk Analysis | ✅ | ✅ |

## Troubleshooting

### "Cannot connect to backend server"
- Make sure `server.py` is running
- Check that the backend is on `localhost:8000`
- Verify no firewall is blocking the connection

### "No devices found"
- Make sure a USB device is connected
- On Windows, check Device Manager
- On Linux/Mac, check `/media` or `/Volumes`

### UI appears blank or frozen
- Check the Activity Log in the Dashboard tab
- Verify backend is responding: `curl http://localhost:8000/api/health`
- Restart both backend and UI

## Notes

- The UI auto-refreshes system health every 5 seconds
- All operations run in background threads to keep UI responsive
- Certificate downloads open in your default browser
- Settings are saved immediately to the backend

## Support

For issues or questions, check:
1. Backend server logs
2. Activity Log in the Dashboard tab
3. Backend API documentation

