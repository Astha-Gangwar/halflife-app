import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import CaptureInput from '../components/CaptureInput'
import { searchItems } from '../services/api'
import type { SavedItem } from '../types/domain'
import { INTENT_LABELS } from '../types/domain'

const Home: React.FC = () => {
  const navigate = useNavigate()
  const [recentItems, setRecentItems] = useState<SavedItem[]>([])

  useEffect(() => {
    searchItems('', 6).then(setRecentItems).catch(() => setRecentItems([]))
  }, [])

  return (
      <main className="container" style={{ paddingBottom: '80px' }}>
        <div style={{ marginBottom: '40px' }}>
          <h1 style={{ fontSize: '2.5rem', marginBottom: '8px' }}>Externalize your mind.</h1>
          <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)' }}>
            A semantic memory engine that understands context, tracks lifecycles, and resurfaces knowledge when you actually need it.
          </p>
        </div>

        <CaptureInput />

        {recentItems.length > 0 && (
          <div style={{ marginTop: '60px' }}>
            <h3 style={{ marginBottom: '16px' }}>Recent Activity</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
              {recentItems.map(item => (
                <div
                  key={item.item_id}
                  className="glass-panel"
                  style={{ padding: '20px', cursor: 'pointer', transition: 'var(--transition-fast)' }}
                  onClick={() => navigate(`/items/${item.item_id}`)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--primary-color)', fontWeight: '600', textTransform: 'uppercase' }}>{INTENT_LABELS[item.intent_type]}</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{new Date(item.created_at).toLocaleDateString()}</span>
                  </div>
                  <h4 style={{ marginBottom: '8px' }}>{item.approved_title}</h4>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {item.approved_summary || item.original_content}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
  )
}

export default Home
