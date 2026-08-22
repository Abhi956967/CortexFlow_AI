import { initializeApp, getApps } from "firebase/app";
import { getAuth, GoogleAuthProvider, GithubAuthProvider } from "firebase/auth";

const apiKey = import.meta.env.VITE_FIREBASE_API_KEY;

const firebaseConfig = {
  apiKey: apiKey && apiKey !== "add your firebase api key" ? apiKey : "AIzaSyDummyKeyForSafeInitOnly12345678",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "cortexflow-ai.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "cortexflow-ai",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "cortexflow-ai.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "1234567890",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:1234567890:web:abcdef"
};

let app;
let auth;
let googleProvider = new GoogleAuthProvider();
let githubProvider = new GithubAuthProvider();

try {
  app = getApps().length > 0 ? getApps()[0] : initializeApp(firebaseConfig);
  auth = getAuth(app);
} catch (e) {
  console.warn("Firebase initialization warning (running in safe fallback mode):", e);
  auth = null;
}

export { auth, googleProvider, githubProvider };