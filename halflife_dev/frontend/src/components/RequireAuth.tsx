import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const RequireAuth: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, initializing } = useAuth()
  // Firebase restores an existing session asynchronously, so a real
  // logged-in user briefly has isAuthenticated === false on first load —
  // wait for that to resolve instead of bouncing them to /login.
  if (initializing && !isAuthenticated) return null
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default RequireAuth
