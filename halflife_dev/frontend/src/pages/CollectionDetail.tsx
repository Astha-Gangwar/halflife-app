import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { listCollections, listCollectionItems, getItem } from '../services/api'
import type { Collection, SavedItem } from '../types/domain'
import { INTENT_LABELS } from '../types/domain'
import { computeCollectionStats } from '../utils/collectionStats'

const CollectionDetail: React.FC = () => {
  const { collectionId } = useParams<{ collectionId: string }>()
  const navigate = useNavigate()
  const [collection, setCollection] = useState<Collection | null>(null)
  const [items, setItems] = useState<SavedItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const stats = useMemo(() => computeCollectionStats(items), [items])

  useEffect(() => {
    if (!collectionId) return
    let cancelled = false
    setLoading(true)
    setError(null)

    Promise.all([
      listCollections(),
      listCollectionItems(collectionId),
    ])
      .then(async ([allCollections, itemIds]) => {
        if (cancelled) return
        setCollection(allCollections.find((c) => c.collection_id === collectionId) ?? null)
        const loadedItems = await Promise.all(itemIds.map((id) => getItem(id)))
        if (!cancelled) setItems(loadedItems)
      })
      .catch((err) => !cancelled && setError(err instanceof Error ? err.message : 'Failed to load collection'))
      .finally(() => !cancelled && setLoading(false))

    return () => { cancelled = true }
  }, [collectionId])

  return (
      <main className="container" style={{ paddingBottom: '80px' }}>
      <div style={{ marginBottom: '24px' }}>
        <button
          type="button"
          style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
          onClick={() => navigate('/collections')}
        >
          ← Back to Collections
        </button>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: '#ff6b6b' }}>{error}</p>}

      {!loading && !error && (
        <>
          <div style={{ marginBottom: '32px' }}>
            <h2 style={{ fontSize: '2.5rem', marginBottom: '8px' }}>{collection?.name ?? 'Collection'}</h2>
            {collection?.description && (
              <p style={{ color: 'var(--text-secondary)' }}>{collection.description}</p>
            )}
          </div>

          {/* Collection KPIs -- computed from this collection's actual items,
              the same lifecycle-state logic the Insights page uses. */}
          <div className="kpi-strip">
            <div className="glass-panel kpi-card">
              <div className="kpi-label">Total Items</div>
              <div className="kpi-value">{stats.items}</div>
            </div>
            <div className="glass-panel kpi-card">
              <div className="kpi-label">Acted On Rate</div>
              <div className="kpi-value">{stats.actedOnRate}%</div>
            </div>
            <div className="glass-panel kpi-card">
              <div className="kpi-label">Ready for Review</div>
              <div className="kpi-value">
                {stats.ready} <span className="kpi-trend" style={{color: 'var(--status-amber)'}}>items</span>
              </div>
            </div>
          </div>

          {/* Collection Insight */}
          {items.length > 0 && (
            <div className="glass-panel" style={{ padding: '24px', marginBottom: '40px', borderLeft: '4px solid var(--primary-color)' }}>
              <h3 style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: 'var(--primary-color)' }}>✧</span> Collection Insight
              </h3>
              <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
                {stats.atRisk > 0
                  ? `${stats.atRisk} of ${stats.items} item${stats.items === 1 ? '' : 's'} in this collection ${stats.atRisk === 1 ? 'has' : 'have'} sat untouched for 14+ days. Consider revisiting or archiving them.`
                  : `You've acted on ${stats.actedOnRate}% of the items in this collection. Last activity: ${stats.lastActivityLabel}.`}
              </p>
            </div>
          )}

          <h3 style={{ marginBottom: '24px' }}>Recommended Next</h3>
          {items.length === 0 && (
            <p style={{ color: 'var(--text-secondary)' }}>Nothing in this collection yet.</p>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
            {items.map((item) => (
              <div
                key={item.item_id}
                className="glass-panel"
                style={{ padding: '24px', cursor: 'pointer', transition: 'var(--transition-fast)' }}
                onClick={() => navigate(`/items/${item.item_id}`)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                  <span className="chip chip-blue">
                    {INTENT_LABELS[item.intent_type] || 'Note'}
                  </span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </div>
                <h3 style={{ marginBottom: '12px', fontSize: '1.25rem' }}>{item.approved_title}</h3>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {item.approved_summary || item.original_content}
                </p>
              </div>
            ))}
          </div>
        </>
      )}
      </main>
  )
}

export default CollectionDetail
