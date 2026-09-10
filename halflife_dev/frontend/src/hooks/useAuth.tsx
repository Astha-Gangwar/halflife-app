import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'
import {
  createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut as firebaseSignOut,
  onAuthStateChanged,
} from 'firebase/auth'
import { firebaseAuth } from '../services/firebase'
import { devLogin, getToken, setToken, clearToken } from '../services/api'

// Matches the backend's DEMO_USER_ID default (backend/security/authentication.py).
// The demo account is server-enforced read-only via require_mutation_allowed;
// this lets the UI hide/disable mutating controls instead of letting every
// action round-trip to a 403.
const DEMO_USER_ID = 'demo'

interface AuthContextValue {
  userId: string | null
  email: string | null
  isAuthenticated: boolean
  isDemo: boolean
  // True only while first resolving whether a real (Firebase) session is
  // already signed in — RequireAuth waits for this before redirecting to
  // /login, since Firebase restores its session asynchronously.
  initializing: boolean
  loginDemo: () => Promise<void>
  signUp: (email: string, password: string) => Promise<void>
  signIn: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

function decodeDemoToken(token: string): { userId: string | null; email: string | null } {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return { userId: payload.sub ?? null, email: payload.email ?? null }
  } catch {
    return { userId: null, email: null }
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const initialDemoToken = getToken()
  const initialDemo = initialDemoToken ? decodeDemoToken(initialDemoToken) : null
  const [userId, setUserId] = useState<string | null>(initialDemo?.userId ?? null)
  const [email, setEmail] = useState<string | null>(initialDemo?.email ?? null)
  const [initializing, setInitializing] = useState(true)

  useEffect(() => {
    if (!firebaseAuth) {
      // Firebase isn't configured (see services/firebase.ts) — the demo
      // account still works via its own token, real accounts just can't
      // sign up/in until VITE_FIREBASE_* env vars are set.
      setInitializing(false)
      return
    }
    const unsubscribe = onAuthStateChanged(firebaseAuth, (firebaseUser) => {
      if (firebaseUser) {
        setUserId(firebaseUser.uid)
        setEmail(firebaseUser.email)
      } else {
        // No Firebase session — fall back to the demo token, if any.
        const token = getToken()
        const decoded = token ? decodeDemoToken(token) : null
        setUserId(decoded?.userId ?? null)
        setEmail(decoded?.email ?? null)
      }
      setInitializing(false)
    })
    return unsubscribe
  }, [])

  const loginDemo = useCallback(async () => {
    const { access_token, user_id } = await devLogin(DEMO_USER_ID)
    setToken(access_token)
    setUserId(user_id)
    setEmail(`${user_id}@example.com`)
  }, [])

  const requireFirebase = () => {
    if (!firebaseAuth) throw new Error('Sign-in with email/password isn\'t configured yet.')
    return firebaseAuth
  }

  const signUp = useCallback(async (emailInput: string, password: string) => {
    const auth = requireFirebase()
    clearToken() // in case a demo session was active
    await createUserWithEmailAndPassword(auth, emailInput, password)
  }, [])

  const signIn = useCallback(async (emailInput: string, password: string) => {
    const auth = requireFirebase()
    clearToken()
    await signInWithEmailAndPassword(auth, emailInput, password)
  }, [])

  const logout = useCallback(async () => {
    clearToken()
    if (firebaseAuth?.currentUser) {
      await firebaseSignOut(firebaseAuth)
    }
    setUserId(null)
    setEmail(null)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        userId, email, isAuthenticated: !!userId, isDemo: userId === DEMO_USER_ID,
        initializing, loginDemo, signUp, signIn, logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
