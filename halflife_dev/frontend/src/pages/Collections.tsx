import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listCollections, createCollection, listCollectionItems, getItem } from '../services/api'
import type { Collection } from '../types/domain'
import { computeCollectionStats, type CollectionStats } from '../utils/collectionStats'

const Collections: React.FC = () => {
  const [collections, setCollections] = useState<Collection[]>([])
  const [stats, setStats] = useState<Record<string, CollectionStats>>({})
  const [newName, setNewName] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const load = () => {
    setLoading(true)
    listCollections()
      .then(async (results) => {
        setCollections(results)
        // Each collection's card needs real item counts/state, not just its
        // own metadata -- fetch membership + item details in parallel per
        // collection, same pattern CollectionDetail already uses.
        const entries = await Promise.all(
          results.map(async (collection) => {
            try {
              const itemIds = await listCollectionItems(collection.collection_id)
              const items = await Promise.all(itemIds.map((id) => getItem(id)))
              return [collection.collection_id, computeCollectionStats(items)] as const
            } catch {
              return [collection.collection_id, computeCollectionStats([])] as const
            }
          })
        )
        setStats(Object.fromEntries(entries))
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load collections'))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName.trim()) return
    try {
      await createCollection(newName.trim())
      setNewName('')
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create collection')
    }
  }

  return (
      <main className="container" style={{ paddingBottom: '80px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <h2 style={{ fontSize: '2.5rem' }}>Collections</h2>
        <form onSubmit={handleCreate} style={{ display: 'flex', gap: '12px' }}>
          <input
            className="input-base"
            placeholder="New collection name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
          />
          <button type="submit" className="btn-primary" disabled={!newName.trim()}>Create</button>
        </form>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p style={{ color: '#ff6b6b' }}>{error}</p>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
        {collections.map((collection) => {
          const s = stats[collection.collection_id]
          return (
            <div
              key={collection.collection_id}
              className="glass-panel"
              style={{ padding: '24px', cursor: 'pointer', display: 'flex', flexDirection: 'column' }}
              onClick={() => navigate(`/collections/${collection.collection_id}`)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '1.4rem', margin: 0 }}>{collection.name}</h3>
                {s && <span className={`chip chip-${s.color}`}>{s.status}</span>}
              </div>

              <div style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '16px', fontFamily: 'Outfit' }}>
                {s ? s.items : '—'} <span style={{ fontSize: '1rem', fontWeight: '500', color: 'var(--text-secondary)' }}>items</span>
              </div>

              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 24px 0', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.9rem' }}>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: 'var(--status-green)' }}>•</span> {s?.ready ?? 0} ready for review
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ color: 'var(--status-amber)' }}>•</span> {s?.atRisk ?? 0} becoming stale
                </li>
              </ul>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: 'auto', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
                <span>{s ? `${s.actedOnRate}% acted on` : '—'}</span>
                <span>Last activity: {s?.lastActivityLabel ?? '—'}</span>
              </div>
            </div>
          )
        })}
      </div>
      {!loading && collections.length === 0 && (
        <p style={{ color: 'var(--text-secondary)' }}>No collections yet — create one above.</p>
      )}
      </main>
  )
}

export default Collections
