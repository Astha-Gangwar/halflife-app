import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getItem, changeItemStatus, listRelationships, listRelationshipCandidates, recordOutcome } from '../services/api'
import type { SavedItem, Relationship, RelationshipCandidate } from '../types/domain'
import { ACTED_ON_STATES, INTENT_LABELS } from '../types/domain'
import { useAuth } from '../hooks/useAuth'

const ItemDetail: React.FC = () => {
  const { itemId } = useParams<{ itemId: string }>()
  const navigate = useNavigate()
  const { isDemo } = useAuth()
  const [item, setItem] = useState<SavedItem | null>(null)
  const [relationships, setRelationships] = useState<Relationship[]>([])
  const [candidates, setCandidates] = useState<RelationshipCandidate[]>([])
  // Candidates only carry a target_item_id and generic supporting_facts --
  // showing "Suggested: similar" for every one of them is meaningless once
  // there's more than one, since nothing distinguishes which real memory
  // each suggestion actually points at. Resolve the target items so the
  // list can show what it's actually suggesting.
  const [candidateItems, setCandidateItems] = useState<Record<string, SavedItem>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionMessage, setActionMessage] = useState<string | null>(null)

  useEffect(() => {
    if (!itemId) return
    let cancelled = false
    setLoading(true)
    Promise.all([getItem(itemId), listRelationships(itemId), listRelationshipCandidates(itemId)])
      .then(async ([fetchedItem, rels, cands]) => {
        if (cancelled) return
        setItem(fetchedItem)
        setRelationships(rels)
        setCandidates(cands)
        const targetIds = Array.from(new Set(cands.map((c) => c.target_item_id)))
        const targets = await Promise.all(targetIds.map((id) => getItem(id).catch(() => null)))
        if (cancelled) return
        setCandidateItems(Object.fromEntries(
          targetIds.map((id, i) => [id, targets[i]]).filter((pair): pair is [string, SavedItem] => pair[1] !== null)
        ))
      })
      .catch((err) => !cancelled && setError(err instanceof Error ? err.message : 'Failed to load item'))
      .finally(() => !cancelled && setLoading(false))
    return () => { cancelled = true }
  }, [itemId])

  const handleStatusChange = async (action: 'archive' | 'restore' | 'delete') => {
    if (!itemId) return
    try {
      const updated = await changeItemStatus(itemId, action)
      if (action === 'delete') {
        // Deleted items no longer show up anywhere in the app (Library,
        // Home, search), and there's no undo in the UI for this one
        // unlike archive/restore -- staying on the page just leaves you
        // looking at content that's effectively gone.
        navigate('/library')
        return
      }
      setItem(updated)
      setActionMessage(`Item ${action}d.`)
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Action failed')
    }
  }

  const handleOutcome = async (outcome: 'tried' | 'completed' | 'dismissed' | 'not_relevant') => {
    if (!itemId) return
    try {
      const result = await recordOutcome(itemId, outcome)
      // The API call already updated the item's lifecycle state server-side
      // -- update it here too, or the status line above (and the rest of
      // this page) keeps showing the old state until a manual reload,
      // making the click look like it silently did nothing.
      setItem((prev) => (prev ? { ...prev, current_lifecycle_state: result.lifecycle_state as SavedItem['current_lifecycle_state'] } : prev))
      setActionMessage(`Outcome recorded: ${result.lifecycle_state}`)
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Failed to record outcome')
    }
  }

  return (
      <main className="container" style={{ paddingBottom: '80px' }}>
        {loading && <p>Loading...</p>}
        {!loading && (error || !item) && <p>{error || 'Item not found'}</p>}
        {!loading && item && (
          <>
        <button className="btn-secondary" style={{ marginBottom: '24px' }} onClick={() => navigate(-1)}>&larr; Back</button>

        <div className="glass-panel" style={{ padding: '32px', marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--primary-color)', fontWeight: 600, textTransform: 'uppercase' }}>
              {INTENT_LABELS[item.intent_type]}
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{item.status} &middot; {item.current_lifecycle_state}</span>
          </div>
          {actionMessage && <p style={{ marginBottom: '12px', color: 'var(--primary-color)', fontSize: '0.9rem' }}>{actionMessage}</p>}
          <h2 style={{ marginBottom: '12px' }}>{item.approved_title}</h2>
          {item.approved_summary && <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>{item.approved_summary}</p>}
          <p style={{ whiteSpace: 'pre-wrap' }}>{item.original_content}</p>
          {item.tags.length > 0 && (
            <div style={{ marginTop: '16px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {item.tags.map((tag) => (
                <span key={tag} style={{ fontSize: '0.75rem', padding: '4px 10px', borderRadius: '999px', border: '1px solid var(--border-color)' }}>{tag}</span>
              ))}
            </div>
          )}
        </div>

        {!isDemo && (
          <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
            <h3 style={{ marginBottom: '16px' }}>Record an outcome</h3>
            {ACTED_ON_STATES.has(item.current_lifecycle_state) ? (
              <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
                Outcome recorded: <b style={{ color: 'var(--text-primary)' }}>{item.current_lifecycle_state.replace('_', ' ')}</b>.
                This won't be suggested for revisit again.
              </p>
            ) : (
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <button className="btn-secondary" onClick={() => handleOutcome('tried')}>Tried it</button>
                <button className="btn-secondary" onClick={() => handleOutcome('completed')}>Completed</button>
                <button className="btn-secondary" onClick={() => handleOutcome('dismissed')}>Not now</button>
                <button className="btn-secondary" onClick={() => handleOutcome('not_relevant')}>Not relevant</button>
              </div>
            )}
          </div>
        )}

        {!isDemo && (
          <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
            <h3 style={{ marginBottom: '16px' }}>Manage</h3>
            <div style={{ display: 'flex', gap: '12px' }}>
              {item.status !== 'archived' && <button className="btn-secondary" onClick={() => handleStatusChange('archive')}>Archive</button>}
              {item.status === 'archived' && <button className="btn-secondary" onClick={() => handleStatusChange('restore')}>Restore</button>}
              <button className="btn-secondary" onClick={() => handleStatusChange('delete')}>Delete</button>
            </div>
            {actionMessage && <p style={{ marginTop: '12px', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{actionMessage}</p>}
          </div>
        )}

        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ marginBottom: '16px' }}>Related memories</h3>
          {relationships.length === 0 && candidates.length === 0 && (
            <p style={{ color: 'var(--text-secondary)' }}>No related memories found yet.</p>
          )}
          {relationships.map((rel) => (
            <div key={rel.relationship_id} style={{ padding: '12px 0', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--secondary-color)' }}>{rel.relationship_type}</span>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{rel.reason}</p>
            </div>
          ))}
          {candidates.map((cand) => {
            const target = candidateItems[cand.target_item_id]
            return (
              <div
                key={cand.candidate_id}
                style={{ padding: '12px 0', borderBottom: '1px solid var(--border-color)', cursor: target ? 'pointer' : 'default' }}
                onClick={() => target && navigate(`/items/${target.item_id}`)}
              >
                <div style={{ fontWeight: 500 }}>{target ? target.approved_title : 'Related memory'}</div>
                {cand.supporting_facts.length > 0 && (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '4px 0 0' }}>
                    {cand.supporting_facts.join(' · ')}
                  </p>
                )}
              </div>
            )
          })}
        </div>
          </>
        )}
      </main>
  )
}

export default ItemDetail
