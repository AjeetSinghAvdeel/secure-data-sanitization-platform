// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getAnalytics } from "firebase/analytics";
import { getFirestore } from "firebase/firestore";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
// Load from environment variables (Vite exposes them as import.meta.env)
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyBqINgmDXGxLM98wfjUz2wxM-lurN_BewA",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "sih2025-5963e.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "sih2025-5963e",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "sih2025-5963e.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "264755982565",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:264755982565:web:c5c00d2dc1bcf0d05c640c",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-6XG2SP4TMP"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const analytics = getAnalytics(app);
export default app;
