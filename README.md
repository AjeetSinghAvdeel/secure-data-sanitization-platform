# Secure Data Sanitization Platform

A comprehensive full-stack application for secure data wiping, device management, and compliance reporting. Built with **FastAPI** (Python backend) and **React/Vite** (TypeScript frontend) with modern security practices.

---

## 🎯 Features

- 🔍 **Device Scanner** – Detect, analyze, and assess risk levels of connected USB devices and storage
- 🧹 **Secure Wipe** – Multi-pass cryptographic data wiping (random overwrite, zero overwrite, DOD 5220.22-M compatible)
- 📜 **Digital Certificates** – Auto-generate tamper-proof PDF certificates for every wipe operation
- 🔐 **Tamper Detection** – RSA-signed certificate verification to prevent tampering
- 📊 **Compliance Dashboard** – Track NIST SP 800-88, GDPR Article 17, and DOD 5220.22-M compliance scores
- 💾 **Firebase Integration** – Secure cloud storage of certificates and audit logs
- 🎨 **Modern UI** – Built with TailwindCSS, shadcn/ui components, and Vite for fast development
- ⚡ **Real-time Health Monitoring** – CPU, memory, disk usage, and device health checks

---

## 📂 Project Structure

```
secure-data-sanitization-platform/
│
├── Backend/
│   ├── Server/                        # FastAPI Backend Application
│   │   ├── server.py                  # Main FastAPI app with all endpoints
│   │   ├── requirements.txt           # Python dependencies
│   │   ├── .env.example               # Environment variables template
│   │   ├── main.py                    # Core wiping & signing logic
│   │   ├── verify_wipe.py             # Post-wipe verification utilities
│   │   ├── certificates.json          # Local certificate metadata
│   │   ├── tamper_db.json             # Tamper detection records
│   │   ├── settings.json              # User settings
│   │   ├── cert_pdfs/                 # Generated certificate PDFs
│   │   ├── __pycache__/               # Python cache
│   │   └── firebase_key.json          # [GITIGNORED] Firebase service account
│   │
│   └── cert_pdfs/                     # Shared certificate storage
│
├── Frontend/
│   └── cyber-wipe-ai-main/            # React + Vite + TypeScript Frontend
│       ├── src/
│       │   ├── App.tsx                # Main app component
│       │   ├── main.tsx               # Entry point
│       │   ├── firebaseConfig.ts      # Firebase config (uses env vars)
│       │   ├── components/            # UI Components
│       │   │   ├── ui/                # shadcn/ui base components
│       │   │   ├── scanning/          # Device scanner components
│       │   │   ├── wiping/            # Secure wipe components
│       │   │   ├── certificates/      # Certificate manager components
│       │   │   ├── compliance/        # Compliance dashboard components
│       │   │   ├── charts/            # Data visualization
│       │   │   └── verification/      # Certificate verification UI
│       │   ├── pages/                 # Route pages
│       │   │   ├── Dashboard.tsx
│       │   │   ├── Landing.tsx
│       │   │   ├── Login.tsx
│       │   │   ├── Register.tsx
│       │   │   └── UsbDemo.tsx
│       │   ├── context/               # React context (Auth, etc)
│       │   ├── hooks/                 # Custom React hooks
│       │   ├── lib/                   # Utilities and helpers
│       │   ├── assets/                # Images, icons, etc
│       │   ├── App.css                # App-level styles
│       │   └── index.css              # Global styles
│       ├── package.json               # NPM dependencies
│       ├── vite.config.ts             # Vite configuration
│       ├── tsconfig.json              # TypeScript config
│       ├── .env.example               # Environment variables template
│       ├── bun.lockb                  # Bun lock file (optional)
│       └── public/                    # Static assets
│
├── .gitignore                         # Git ignore rules (env, keys, node_modules, etc)
├── README.md                          # This file
└── LICENSE                            # MIT License

```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+** (for backend)
- **Node.js 16+** (for frontend)
- **Git**
- **Firebase Account** (optional, for cloud features)

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd Backend/Server
```

2. **Create Python virtual environment:**
```bash
python -m venv venv
source venv/bin/activate       # macOS/Linux
# or
venv\Scripts\activate          # Windows
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
cp .env.example .env.local
```

Edit `.env.local` and add your Firebase service account JSON:
```bash
FIREBASE_KEY_JSON='{"type":"service_account","project_id":"...","private_key":"..."}'
```

5. **Run the server:**
```bash
python server.py
# or with uvicorn
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Server will be available at: **http://localhost:8000**
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **ReDoc:** http://localhost:8000/redoc

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd Frontend/cyber-wipe-ai-main
```

2. **Install dependencies:**
```bash
npm install
```

3. **Set up environment variables:**
```bash
cp .env.example .env.local
```

Edit `.env.local` with your Firebase web config (all values are optional if you only want local mode):
```bash
VITE_FIREBASE_API_KEY=AIzaSyBq...
VITE_FIREBASE_AUTH_DOMAIN=project.firebaseapp.com
# ... etc
```

4. **Start development server:**
```bash
npm run dev
```

Frontend will be available at: **http://localhost:8080** (or as shown in terminal)

---

## 🔐 Security Features

- **Environment-based secrets:** All sensitive credentials loaded from `.env.local` (never committed to git)
- **Tamper-proof certificates:** RSA-2048 signed digital certificates for every wipe operation
- **Multi-pass wiping:** Support for DOD 5220.22-M compliant 3-pass and random overwrite patterns
- **Compliance tracking:** Monitor NIST, GDPR, and DOD standards adherence
- **Firebase integration:** Cloud-backed certificate storage with audit trails
- **Rotated credentials:** Service account and API keys are regularly rotated

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Server status |
| `GET` | `/api/health` | System health (CPU, memory, disk) |
| `GET` | `/api/settings` | Get application settings |
| `POST` | `/api/settings` | Update settings |
| `GET` | `/devices` | List connected USB devices |
| `GET` | `/system-analysis` | Analyze system storage |
| `POST` | `/wipe-usb` | Start secure wipe operation |
| `GET` | `/api/certificates` | List all certificates |
| `GET` | `/api/certificates/{cert_id}` | Get specific certificate |
| `GET` | `/api/certificates/download/{cert_id}` | Download certificate PDF |
| `GET` | `/compliance` | Compliance scores (NIST, GDPR, DOD) |
| `GET` | `/tamper/verify/{cert_id}` | Verify certificate integrity |
| `/docs` | Swagger UI | Interactive API documentation |

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** – Modern, fast Python web framework
- **Uvicorn** – ASGI server
- **Firebase Admin SDK** – Cloud database and auth
- **Cryptography** – RSA signing and hashing
- **ReportLab** – PDF certificate generation
- **psutil** – System monitoring
- **python-dotenv** – Environment variable management

### Frontend
- **React 18** – UI library
- **TypeScript** – Type-safe JavaScript
- **Vite** – Build tool and dev server
- **TailwindCSS** – Utility-first CSS framework
- **shadcn/ui** – Accessible component library
- **Firebase SDK** – Authentication and Firestore

---

## 📝 Configuration

### Backend Environment Variables (`.env.local`)
```bash
# Firebase service account (as JSON string)
FIREBASE_KEY_JSON='{"type":"service_account",...}'

# Server
PORT=8000
HOST=0.0.0.0
```

### Frontend Environment Variables (`.env.local`)
```bash
# Firebase Web Config (all optional)
VITE_FIREBASE_API_KEY=AIzaSy...
VITE_FIREBASE_AUTH_DOMAIN=project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=project-id
VITE_FIREBASE_STORAGE_BUCKET=project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123:web:abc
VITE_FIREBASE_MEASUREMENT_ID=G-XXXXX
```

---

## 🧪 Testing

### Backend Test
```bash
cd Backend/Server
python test_server.py
```

### Check Available Endpoints
```bash
cd Backend/Server
python check_endpoints.py
```

---

## 🔄 Development Workflow

1. **Start backend:**
```bash
cd Backend/Server
source venv/bin/activate
python server.py
```

2. **Start frontend (in another terminal):**
```bash
cd Frontend/cyber-wipe-ai-main
npm run dev
```

3. **Make changes** to React components or FastAPI endpoints
4. **HMR (Hot Module Reload)** will automatically refresh the browser
5. **Commit with meaningful messages:**
```bash
git add .
git commit -m "feat: add new device analysis feature"
git push origin main
```

---

## 🚨 Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version

# Verify dependencies
pip list | grep -E "fastapi|uvicorn|firebase"

# Check if port 8000 is in use
lsof -i :8000
```

### Frontend won't build
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version
```

### Firebase errors
- Ensure `.env.local` has valid `FIREBASE_KEY_JSON`
- Check Firebase project settings in Google Cloud Console
- Verify service account has Firestore access

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Firebase Documentation](https://firebase.google.com/docs)
- [NIST SP 800-88 (Digital Forensics)](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication800-88.pdf)

---

## 📄 License

This project is licensed under the **MIT License**. See [LICENSE](./LICENSE) file for details.

---

## 👨‍💻 Authors & Contributors

- **Ajeet Singh Avdeel** – Project Lead

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## ⚠️ Important Security Notes

- **Never commit `.env` files** – Keep credentials in `.env.local` (gitignored)
- **Rotate keys regularly** – Replace Firebase keys every 90 days
- **Use strong passwords** – For database and cloud accounts
- **Enable 2FA** – On GitHub and Google Cloud accounts
- **Review dependencies** – Keep npm and pip packages updated

---

## 📞 Support & Contact

For issues, questions, or suggestions:
1. Check existing [GitHub Issues](https://github.com/AjeetSinghAvdeel/secure-data-sanitization-platform/issues)
2. Open a new issue with details
3. Contact: ajeet.singh@example.com (update with actual contact)

---

**Last Updated:** December 31, 2025  
**Version:** 1.0.0
