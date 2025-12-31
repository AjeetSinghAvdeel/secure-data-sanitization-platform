# Troubleshooting "Not Found" Errors

## Common Causes and Solutions

### 1. Server Not Running
**Symptom**: Connection refused errors or "Cannot connect to server"

**Solution**:
```bash
cd Backend\India
python server.py
```

The server should start on `http://localhost:8000`

### 2. Wrong Endpoint Path
**Symptom**: 404 "Not Found" error with specific endpoint

**Solution**: Check the endpoint list:
- `GET /` - Root endpoint
- `GET /api/health` - Health check
- `GET /api/settings` - Get settings
- `POST /api/settings` - Update settings
- `GET /devices` - List devices
- `GET /api/certificates` - List certificates
- `POST /wipe-usb` - Wipe device
- `GET /compliance` - Compliance scores
- `GET /tamper/verify/{cert_id}` - Verify certificate

### 3. Check Available Endpoints
Run the endpoint checker:
```bash
python check_endpoints.py
```

This will test all endpoints and show which ones are working.

### 4. View API Documentation
Open in browser:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 5. Better Error Messages
The server now provides detailed 404 error messages that include:
- The exact endpoint that was not found
- A list of all available endpoints
- Hints for debugging

### 6. Common Issues

#### Settings Endpoint
If you get validation errors on `/api/settings` POST:
- Make sure you're sending JSON with these fields:
  - `wipeMethod`: string (e.g., "3-pass")
  - `generateCerts`: boolean
  - `includeQRCode`: boolean
  - `compliance`: string
  - `tamperDetection`: boolean

#### Certificate Endpoints
If `/api/certificates` returns empty:
- This is normal if Firebase is not initialized
- Check if `firebase_key.json` exists
- Server will work without Firebase, but certificates won't be saved

#### Device Detection
If `/devices` returns empty:
- Make sure a USB device is connected
- On Windows, check Device Manager
- The endpoint will return an empty list if no removable devices are found

## Testing the Server

1. **Start the server**:
   ```bash
   python server.py
   ```

2. **Test with curl** (if available):
   ```bash
   curl http://localhost:8000/api/health
   ```

3. **Or use the test script**:
   ```bash
   python test_server.py
   ```

4. **Check endpoints**:
   ```bash
   python check_endpoints.py
   ```

## Getting Help

If you're still getting errors:
1. Check the server console output for error messages
2. Look at the detailed 404 response (it shows available endpoints)
3. Verify the server is running on port 8000
4. Check that all dependencies are installed:
   ```bash
   pip install fastapi uvicorn psutil firebase-admin cryptography reportlab requests
   ```

