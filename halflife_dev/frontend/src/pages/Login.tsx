import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const FRIENDLY_ERRORS: Record<string, string> = {
  'auth/email-already-in-use': 'An account already exists for that email — try logging in instead.',
  'auth/invalid-email': 'That doesn\'t look like a valid email address.',
  'auth/weak-password': 'Password must be at least 6 characters.',
  'auth/wrong-password': 'Incorrect password.',
  'auth/invalid-credential': 'Incorrect email or password.',
  'auth/user-not-found': 'No account found for that email — sign up first.',
  'auth/too-many-requests': 'Too many attempts — try again in a bit.',
}

function friendlyMessage(err: unknown): string {
  const code = (err as { code?: string })?.code
  if (code && FRIENDLY_ERRORS[code]) return FRIENDLY_ERRORS[code]
  return err instanceof Error ? err.message : 'Something went wrong'
}

const Login: React.FC = () => {
  const [mode, setMode] = useState<'signIn' | 'signUp'>('signIn')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { signIn, signUp, loginDemo } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !password) return
    setIsSubmitting(true)
    setError(null)
    try {
      if (mode === 'signUp') {
        await signUp(email.trim(), password)
      } else {
        await signIn(email.trim(), password)
      }
      navigate('/')
    } catch (err) {
      setError(friendlyMessage(err))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleViewDemo = async () => {
    setIsSubmitting(true)
    setError(null)
    try {
      await loginDemo()
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load the demo')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="glass-panel" style={{ padding: '40px', width: '100%', maxWidth: '400px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '32px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'linear-gradient(135deg, var(--primary-color), var(--secondary-color))' }}></div>
          <h2 style={{ margin: 0 }}>HalfLife</h2>
        </div>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
          {mode === 'signUp'
            ? 'Create an account with an email and password — only you will be able to sign back in and see your data.'
            : 'Sign in with your email and password.'}
        </p>
        <form onSubmit={handleSubmit}>
          <input
            className="input-base"
            style={{ marginBottom: '12px' }}
            type="email"
            placeholder="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isSubmitting}
            autoFocus
            required
          />
          <input
            className="input-base"
            style={{ marginBottom: '16px' }}
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isSubmitting}
            minLength={6}
            required
          />
          {error && <p style={{ color: '#ff6b6b', marginBottom: '16px', fontSize: '0.9rem' }}>{error}</p>}
          <button type="submit" className="btn-primary" style={{ width: '100%' }} disabled={isSubmitting || !email.trim() || !password}>
            {isSubmitting ? (mode === 'signUp' ? 'Creating account...' : 'Signing in...') : (mode === 'signUp' ? 'Create account' : 'Log in')}
          </button>
        </form>
        <p style={{ textAlign: 'center', marginTop: '16px', fontSize: '0.9rem' }}>
          {mode === 'signUp' ? 'Already have an account?' : "Don't have an account?"}{' '}
          <button
            type="button"
            onClick={() => { setMode(mode === 'signUp' ? 'signIn' : 'signUp'); setError(null) }}
            style={{ background: 'none', border: 'none', color: 'var(--primary-color)', cursor: 'pointer', padding: 0, font: 'inherit' }}
          >
            {mode === 'signUp' ? 'Log in' : 'Sign up'}
          </button>
        </p>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: '20px 0' }}>
          <div style={{ flex: 1, height: '1px', background: 'var(--border-color)' }} />
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>or</span>
          <div style={{ flex: 1, height: '1px', background: 'var(--border-color)' }} />
        </div>
        <button
          type="button"
          className="btn-secondary"
          style={{ width: '100%' }}
          onClick={handleViewDemo}
          disabled={isSubmitting}
        >
          View Demo
        </button>
        <p style={{ color: 'var(--text-secondary)', marginTop: '10px', fontSize: '0.8rem', textAlign: 'center' }}>
          Browse a populated account with sample memories already saved — read-only, so nothing you click here changes it for the next visitor.
        </p>
        <p style={{ color: 'var(--text-secondary)', marginTop: '4px', fontSize: '0.8rem', textAlign: 'center' }}>
          Evaluating this app? Sign in (or view the demo), then open <b>Test Prompts</b> from the profile menu.
        </p>
      </div>
    </div>
  )
}

export default Login
