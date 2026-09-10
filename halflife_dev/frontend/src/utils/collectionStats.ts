import type { SavedItem } from '../types/domain'
import { ACTED_ON_STATES } from '../types/domain'

// Stale-threshold logic mirrors backend/services/insights_service.py's,
// computed client-side since collection membership is already resolved into
// full SavedItem objects on the pages that use this.
const STALE_THRESHOLD_DAYS = 14

export interface CollectionStats {
  items: number
  ready: number
  atRisk: number
  actedOnRate: number
  lastActivityLabel: string
  status: string
  color: 'green' | 'amber' | 'blue'
}

export function computeCollectionStats(items: SavedItem[]): CollectionStats {
  const total = items.length
  const actedOn = items.filter((i) => ACTED_ON_STATES.has(i.current_lifecycle_state))
  const active = items.filter((i) => !ACTED_ON_STATES.has(i.current_lifecycle_state))
  const atRisk = active.filter((i) => daysSince(i.created_at) >= STALE_THRESHOLD_DAYS)
  const ready = active.length - atRisk.length
  const actedOnRate = total ? Math.round((100 * actedOn.length) / total) : 0

  const mostRecentMs = items.reduce((latest, i) => {
    const t = new Date(i.created_at).getTime()
    return t > latest ? t : latest
  }, 0)

  let status = 'Growing quickly'
  let color: CollectionStats['color'] = 'blue'
  if (total === 0) {
    status = 'Empty'
    color = 'blue'
  } else if (atRisk.length > 0 && atRisk.length >= ready) {
    status = 'Needs attention'
    color = 'amber'
  } else if (actedOnRate >= 40) {
    status = 'Healthy'
    color = 'green'
  }

  return {
    items: total,
    ready,
    atRisk: atRisk.length,
    actedOnRate,
    lastActivityLabel: mostRecentMs ? formatRelative(mostRecentMs) : 'No activity yet',
    status,
    color,
  }
}

function daysSince(isoDate: string): number {
  return (Date.now() - new Date(isoDate).getTime()) / 86_400_000
}

function formatRelative(ms: number): string {
  const days = Math.floor((Date.now() - ms) / 86_400_000)
  if (days <= 0) return 'today'
  if (days === 1) return '1 day ago'
  if (days < 7) return `${days} days ago`
  const weeks = Math.floor(days / 7)
  return weeks === 1 ? '1 week ago' : `${weeks} weeks ago`
}
