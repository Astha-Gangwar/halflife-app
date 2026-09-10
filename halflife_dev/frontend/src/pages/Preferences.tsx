import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { getPreferences, updatePreferences } from '../services/api'
import type { UserPreference } from '../types/domain'

const REVIEW_PERIODS: { value: string; label: string }[] = [
  { value: 'morning', label: 'Morning' },
  { value: 'afternoon', label: 'Afternoon' },
  { value: 'evening', label: 'Evening' },
]

// Fall back to a small, common list if the runtime doesn't support
// Intl.supportedValuesOf (older browsers, or a TS lib target that predates it).
const COMMON_TIMEZONES = [
  'UTC', 'America/New_York', 'America/Los_Angeles', 'America/Chicago',
  'Europe/London', 'Europe/Berlin', 'Asia/Kolkata', 'Asia/Dubai',
  'Asia/Singapore', 'Asia/Tokyo', 'Australia/Sydney',
]

function listTimezones(): string[] {
  const intlAny = Intl as unknown as { supportedValuesOf?: (key: string) => string[] }
  return intlAny.supportedValuesOf ? intlAny.supportedValuesOf('timeZone') : COMMON_TIMEZONES
}

const Preferences: React.FC = () => {
  const { logout, isDemo } = useAuth()
  const navigate = useNavigate()

  const [preferences, setPreferences] = useState<UserPreference | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    getPreferences()
      .then(setPreferences)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load preferences'))
      .finally(() => setLoading(false))
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const save = async (patch: Partial<UserPreference>) => {
    if (!preferences || isDemo) return
    const previous = preferences
    setPreferences({ ...preferences, ...patch })
    setSaving(true)
    try {
      const updated = await updatePreferences(patch)
      setPreferences(updated)
    } catch (err) {
      setPreferences(previous)
      setError(err instanceof Error ? err.message : 'Failed to save preference')
    } finally {
      setSaving(false)
    }
  }

  const dailyLimit = preferences?.revisit_frequency_limit ?? 3

  return (
      <main className="container" style={{ maxWidth: '800px', paddingBottom: '80px' }}>
      <div style={{ marginBottom: '40px' }}>
        <h2 style={{ fontSize: '2.5rem', marginBottom: '8px' }}>Preferences</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Manage how Halflife resurfaces your mind.</p>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: '#ff6b6b' }}>{error}</p>}
      {isDemo && (
        <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
          Preferences are read-only in the demo account — sign in with your own account to change them.
        </p>
      )}

      {!loading && preferences && (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>

        {/* Revisit Preferences */}
        <section>
          <h3 style={{ marginBottom: '16px', fontSize: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>Revisit Preferences</h3>

          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <div style={{ fontWeight: '500', marginBottom: '4px' }}>Daily Revisit Limit</div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  How many items can resurface for review per day.
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'rgba(0,0,0,0.2)', padding: '4px 8px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <button
                  disabled={isDemo || saving}
                  onClick={() => save({ revisit_frequency_limit: Math.max(1, dailyLimit - 1) })}
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: isDemo ? 'default' : 'pointer', padding: '4px 8px' }}
                >−</button>
                <span style={{ fontWeight: '600', minWidth: '20px', textAlign: 'center' }}>{dailyLimit}</span>
                <button
                  disabled={isDemo || saving}
                  onClick={() => save({ revisit_frequency_limit: dailyLimit + 1 })}
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: isDemo ? 'default' : 'pointer', padding: '4px 8px' }}
                >+</button>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: '500', marginBottom: '4px' }}>Preferred Review Time</div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  When should we prepare your daily stack?
                </div>
              </div>
              <select
                className="input-base"
                style={{ width: 'auto' }}
                disabled={isDemo || saving}
                value={preferences.preferred_review_period ?? ''}
                onChange={(e) => save({ preferred_review_period: e.target.value || null })}
              >
                <option value="">No preference</option>
                {REVIEW_PERIODS.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
          </div>
        </section>

        {/* Account and Data */}
        <section>
          <h3 style={{ marginBottom: '16px', fontSize: '1.25rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>Account & Data</h3>
          <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: '500', marginBottom: '4px' }}>Timezone</div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{preferences.timezone}</div>
              </div>
              <select
                className="input-base"
                style={{ width: 'auto' }}
                disabled={isDemo || saving}
                value={preferences.timezone}
                onChange={(e) => save({ timezone: e.target.value })}
              >
                {listTimezones().map((tz) => (
                  <option key={tz} value={tz}>{tz}</option>
                ))}
              </select>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--border-color)' }}>
              <div>
                <div style={{ fontWeight: '500', color: 'var(--status-red)', marginBottom: '4px' }}>Sign Out</div>
              </div>
              <button className="btn-secondary" style={{ color: 'var(--status-red)', borderColor: 'var(--status-red-bg)' }} onClick={handleLogout}>Sign Out</button>
            </div>
          </div>
        </section>

      </div>
      )}
      </main>
  )
}

export default Preferences
