import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { searchItems, recordOutcome } from '../services/api'
import type { SavedItem } from '../types/domain'
import { ACTED_ON_STATES, INTENT_LABELS } from '../types/domain'
import { useAuth } from '../hooks/useAuth'

const Library: React.FC = () => {
  const [items, setItems] = useState<SavedItem[]>([])
  const [searchParams] = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('q') ?? '')
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const { isDemo } = useAuth()

  const load = () => {
    let cancelled = false
    setLoading(true)
    searchItems(query)
      .then((results) => !cancelled && setItems(results))
      .catch(() => {})
      .finally(() => !cancelled && setLoading(false))
    return () => { cancelled = true }
  }

  useEffect(load, [query])

  // Navbar search navigates to /library?q=... while Library may already be
  // mounted (shared Layout/<Outlet>), so the initial-state read above won't
  // pick up a later search -- sync whenever the URL's q param changes too.
  useEffect(() => {
    const q = searchParams.get('q') ?? ''
    setQuery(q)
  }, [searchParams])

  const handleComplete = async (e: React.MouseEvent, itemId: string) => {
    e.stopPropagation()
    try {
      const result = await recordOutcome(itemId, 'completed')
      // Update in place immediately -- waiting on a full reload gave no
      // visible feedback at all, since nothing in this row previously
      // rendered lifecycle state, making a successful click look like it
      // silently did nothing.
      setItems((prev) => prev.map((item) =>
        item.item_id === itemId
          ? { ...item, current_lifecycle_state: result.lifecycle_state as SavedItem['current_lifecycle_state'] }
          : item
      ))
    } catch {
      // best-effort; the row stays as-is if this fails
    }
  }

  return (
      <main className="container" style={{ paddingBottom: '80px' }}>
        {/* Top-level KPI strip */}
        <div className="kpi-strip">
          <div className="glass-panel kpi-card">
            <div className="kpi-label">Total Saved</div>
            <div className="kpi-value">{items.length}</div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
          <input
            type="text"
            className="input-base"
            placeholder="Search saved items..."
            style={{ flex: '1', minWidth: '250px' }}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        <div className="glass-panel" style={{ padding: '0', overflow: 'hidden' }}>
          {loading ? (
            <div style={{ padding: '24px', textAlign: 'center' }}>Loading...</div>
          ) : items.length > 0 ? (
            items.map(item => (
              <div
                key={item.item_id}
                className="compact-row"
                style={{ cursor: 'pointer' }}
                onClick={() => navigate(`/items/${item.item_id}`)}
              >
                <div style={{ minWidth: '100px' }}>
                  <span className="chip chip-blue">{INTENT_LABELS[item.intent_type] || 'Note'}</span>
                </div>
                <div>
                  <div className="row-title">{item.approved_title}</div>
                  <div className="row-meta">
                    <span>{item.category || 'Uncategorized'}</span>
                    <span>·</span>
                    <span>Saved {new Date(item.created_at).toLocaleDateString()}</span>
                    {ACTED_ON_STATES.has(item.current_lifecycle_state) && (
                      <>
                        <span>·</span>
                        <span style={{ color: 'var(--status-green, #4ade80)' }}>{item.current_lifecycle_state.replace('_', ' ')}</span>
                      </>
                    )}
                  </div>
                </div>
                <div className="row-actions">
                  <button className="btn-secondary" style={{ padding: '4px 12px', fontSize: '0.85rem' }} onClick={(e) => { e.stopPropagation(); navigate(`/items/${item.item_id}`) }}>Open</button>
                  {!isDemo && !ACTED_ON_STATES.has(item.current_lifecycle_state) && (
                    <button className="btn-secondary" style={{ padding: '4px 12px', fontSize: '0.85rem' }} onClick={(e) => handleComplete(e, item.item_id)}>Complete</button>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>
              No items found.
            </div>
          )}
        </div>
      </main>
  )
}

export default Library
