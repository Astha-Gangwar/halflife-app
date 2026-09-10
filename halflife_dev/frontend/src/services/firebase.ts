import { initializeApp } from 'firebase/app'
import { getAuth, type Auth } from 'firebase/auth'

// From Firebase Console → Project settings → General → Your apps → Web app
// (a Firebase Web API key is not a secret — it's fine to ship in the
// bundle, access is controlled by Firestore security rules and by the
// backend's own Firebase Admin token verification, not by hiding this).
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

export const firebaseConfigured = Object.values(firebaseConfig).every((v) => !!v)

// Firebase throws synchronously (not just on first real call) if the API
// key is missing or malformed — without this guard, an unconfigured
// deployment would crash on the very first import of this module,
// breaking even the demo account, which needs no Firebase config at all.
export const firebaseAuth: Auth | null = firebaseConfigured
  ? getAuth(initializeApp(firebaseConfig))
  : null
