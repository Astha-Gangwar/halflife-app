import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getRevisitCandidates, recordOutcome, getItem } from '../services/api'
import type { ResurfacingCandidate, SavedItem } from '../types/domain'
import { INTENT_LABELS } from '../types/domain'
import { useAuth } from '../hooks/useAuth'

const REASON_LABELS: Record<string, string> = {
  PREFERRED_RECIPE_DAY: 'Today is one of your recipe days',
  TASK_DUE_SOON: 'Due soon',
  TASK_OVERDUE: 'Overdue',
  LEARNING_ITEM_AGED: "You haven't gotten to this yet",
  IDEA_INACTIVE: "You haven't developed this idea in a while",
  MANUAL_REVISIT: 'Worth another look',
}

const Revisit: React.FC = () => {
  const [candidates, setCandidates] = useState<ResurfacingCandidate[]>([])
  const [items, setItems] = useState<Record<string, SavedItem>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const { isDemo } = useAuth()

  useEffect(() => {
    let cancelled = false
    getRevisitCandidates()
      .then(async (results) => {
        if (cancelled) return
        setCandidates(results)
        const loadedItems = await Promise.all(
          results.map((c) => getItem(c.item_id).catch(() => null))
        )
        if (cancelled) return
        const byId: Record<string, SavedItem> = {}
        loadedItems.forEach((item) => { if (item) byId[item.item_id] = item })
        setItems(byId)
      })
      .catch((err) => !cancelled && setError(err instanceof Error ? err.message : 'Failed to load revisit candidates'))
      .finally(() => !cancelled && setLoading(false))
    return () => { cancelled = true }
  }, [])

  const handleOutcome = async (candidate: ResurfacingCandidate, outcome: 'tried' | 'completed' | 'dismissed' | 'not_relevant') => {
    try {
      await recordOutcome(candidate.item_id, outcome)
      setCandidates((prev) => prev.filter((c) => c.resurfacing_id !== candidate.resurfacing_id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to record outcome')
    }
  }

  return (
      <main className="container" style={{ paddingBottom: '80px' }}>
        <h2 style={{ fontSize: '2.5rem', marginBottom: '12px' }}>Time to revisit</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>
          These are eligible based on your lifecycle policy — not everything, just what's actually due.
        </p>

        {loading && <p>Loading...</p>}
        {error && <p style={{ color: '#ff6b6b' }}>{error}</p>}
        {!loading && candidates.length === 0 && !error && (
          <div className="glass-panel" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            Nothing eligible for revisit right now.
          </div>
        )}

        <div className="glass-panel" style={{ padding: '0', overflow: 'hidden' }}>
          {candidates.map((candidate) => {
            const item = items[candidate.item_id]
            return (
              <div
                key={candidate.resurfacing_id}
                className="compact-row"
                style={{ flexDirection: 'column', alignItems: 'stretch', gap: '12px' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px' }}>
                  <div style={{ cursor: 'pointer', flex: 1 }} onClick={() => navigate(`/items/${candidate.item_id}`)}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      {item && <span className="chip chip-blue">{INTENT_LABELS[item.intent_type] || 'Note'}</span>}
                      <span style={{ fontSize: '0.8rem', color: 'var(--primary-color)', fontWeight: 600 }}>
                        {REASON_LABELS[candidate.eligibility_reason_code] || candidate.eligibility_reason_code}
                      </span>
                    </div>
                    <div className="row-title">{item ? item.approved_title : 'Loading item…'}</div>
                    {item && (item.approved_summary || item.original_content) && (
                      <p style={{
                        margin: '4px 0 0', fontSize: '0.9rem', color: 'var(--text-secondary)',
                        display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden',
                      }}>
                        {item.approved_summary || item.original_content}
                      </p>
                    )}
                  </div>
                </div>
                {!isDemo && (
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    <button className="btn-primary" onClick={() => handleOutcome(candidate, 'tried')}>Tried it</button>
                    <button className="btn-secondary" onClick={() => handleOutcome(candidate, 'completed')}>Completed</button>
                    <button className="btn-secondary" onClick={() => handleOutcome(candidate, 'dismissed')}>Not now</button>
                    <button className="btn-secondary" onClick={() => handleOutcome(candidate, 'not_relevant')}>Not relevant</button>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </main>
  )
}

export default Revisit
