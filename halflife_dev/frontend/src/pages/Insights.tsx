import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { getInsightsSummary } from '../services/api'
import type { InsightsSummary } from '../types/domain'

// Static content shown for the demo account — it's a sample dataset, not a
// real user's saving behavior, so real computed metrics wouldn't mean much.
const DEMO_SUMMARY: InsightsSummary = {
  total_saved: 48,
  consumption_rate: 38,
  active_backlog: 47,
  stale_backlog: 8,
  stale_backlog_rate: 17,
  revisit_success_rate: 64,
  category_performance: [
    { category: 'Tech learning', total: 10, acted_on_rate: 62 },
    { category: 'Recipes', total: 8, acted_on_rate: 48 },
    { category: 'Ideas', total: 6, acted_on_rate: 21 },
  ],
  behavior_insights: [
    'You complete short items most often on weekday evenings.',
    'Items with a clear saving intent are acted on more often.',
    'Product research becomes irrelevant faster than your other content.',
    'You saved more than you completed this week, increasing the backlog by four items.',
  ],
}

const Insights = () => {
  const { isDemo } = useAuth()
  const [summary, setSummary] = useState<InsightsSummary | null>(isDemo ? DEMO_SUMMARY : null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isDemo) return
    getInsightsSummary()
      .then(setSummary)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load insights'))
  }, [isDemo])

  return (
      <main className="container mt-8" style={{ paddingBottom: '80px' }}>
      <h1 className="mb-4">Insights</h1>
      <p className="text-secondary mb-8">Is your saving behavior improving?</p>

      {error && <p style={{ color: '#ff6b6b' }}>{error}</p>}
      {!summary && !error && <p>Loading...</p>}

      {summary && (
        <>
          {/* Primary KPIs */}
          <div className="kpi-strip">
            <div className="glass-panel kpi-card">
              <div className="kpi-label">Consumption Rate</div>
              <div className="kpi-value">{summary.consumption_rate}%</div>
            </div>
            <div className="glass-panel kpi-card">
              <div className="kpi-label">Active Backlog</div>
              <div className="kpi-value">{summary.active_backlog} items</div>
            </div>
            <div className="glass-panel kpi-card">
              <div className="kpi-label">Stale Backlog</div>
              <div className="kpi-value">{summary.stale_backlog_rate}%</div>
            </div>
            <div className="glass-panel kpi-card">
              <div className="kpi-label">Revisit Success</div>
              <div className="kpi-value">
                {summary.revisit_success_rate === null ? '—' : `${summary.revisit_success_rate}%`}
              </div>
            </div>
          </div>

          <div className="grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3>Category Performance</h3>
              {summary.category_performance.length === 0 && (
                <p style={{ color: 'var(--text-secondary)' }}>Not enough data yet.</p>
              )}
              {summary.category_performance.map((row) => (
                <div className="compact-row" key={row.category}>
                  <div>{row.category}</div>
                  <div style={{ textAlign: 'right', width: '100%' }}>{row.acted_on_rate}% acted on</div>
                </div>
              ))}
            </div>

            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3>Behavior Insight</h3>
              <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
                {summary.behavior_insights.map((line, i) => <li key={i}>{line}</li>)}
              </ul>
            </div>
          </div>
        </>
      )}
      </main>
  );
};

export default Insights;
