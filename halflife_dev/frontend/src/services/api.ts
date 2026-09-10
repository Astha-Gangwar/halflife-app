import type {
  SavedItem, ResurfacingCandidate, UserPreference, Collection,
  Relationship, RelationshipCandidate, Feedback, IntentType, OutcomeType, InsightsSummary,
} from '../types/domain'
import { firebaseAuth } from './firebase'

// Defaults to '' (a relative path) — correct for single-container
// deployment, where the backend serves this built frontend itself, so API
// calls are same-origin. Local `npm run dev` overrides this via
// .env.development (the frontend and backend run as two separate dev
// servers on two different ports locally, so it needs an absolute URL).
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const TOKEN_STORAGE_KEY = 'halflife_access_token'

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY)
  } catch {
    return null
  }
}

export function setToken(token: string) {
  try {
    localStorage.setItem(TOKEN_STORAGE_KEY, token)
  } catch {
    // localStorage unavailable (private mode etc.) — session just won't persist
  }
}

export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
  } catch {
    // ignore
  }
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// The demo account's token lives in localStorage (see setToken/getToken
// above) and never changes. A real account's token is a Firebase ID
// token, which expires hourly — getIdToken() returns the cached one and
// only refreshes it over the network when it's actually close to expiry,
// so calling it on every request is cheap.
async function getAuthToken(): Promise<string | null> {
  const demoToken = getToken()
  if (demoToken) return demoToken
  if (firebaseAuth?.currentUser) {
    try {
      return await firebaseAuth.currentUser.getIdToken()
    } catch {
      return null
    }
  }
  return null
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await getAuthToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })

  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      detail = body.detail || detail
    } catch {
      // response wasn't JSON
    }
    throw new ApiError(response.status, typeof detail === 'string' ? detail : JSON.stringify(detail))
  }

  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

// --- Auth ---
export async function devLogin(userId: string): Promise<{ access_token: string; user_id: string }> {
  return request('/auth/dev-login', { method: 'POST', body: JSON.stringify({ user_id: userId }) })
}

// --- Capture ---
export interface CaptureResponse {
  status: string
  message: string
  // Whether the agent actually called create_item during this turn — the
  // message text alone isn't a reliable signal (it can sound like a save
  // happened when it didn't, e.g. an agent asking a clarifying question
  // vs. asking for a follow-up correction look similar in prose). Use this
  // field, not string-matching the message, to decide whether to show
  // confirm/correct controls.
  item_created: boolean
  item_id: string | null
  // True only when the agent's response is its fixed out-of-scope refusal
  // -- there is no pending classification to confirm or correct in that
  // case, unlike a genuine clarifying question.
  is_refusal?: boolean
}

export async function captureContent(content: string, idempotencyKey: string): Promise<CaptureResponse> {
  return request('/capture/', { method: 'POST', body: JSON.stringify({ content, idempotency_key: idempotencyKey }) })
}

export async function confirmCapture(originalContent: string, corrections?: Record<string, unknown>): Promise<CaptureResponse> {
  return request('/capture/confirm', {
    method: 'POST',
    body: JSON.stringify({ original_content: originalContent, corrections }),
  })
}

// --- Items ---
export async function createItem(item: Partial<SavedItem> & {
  user_id: string; original_content: string; approved_title: string
  intent_type: IntentType; approved_analysis_id: string
}): Promise<SavedItem> {
  return request('/items/', { method: 'POST', body: JSON.stringify(item) })
}

export async function searchItems(query = '', limit = 50): Promise<SavedItem[]> {
  const params = new URLSearchParams({ query, limit: String(limit) })
  return request(`/items/?${params.toString()}`)
}

export async function getItem(itemId: string): Promise<SavedItem> {
  return request(`/items/${itemId}`)
}

export async function updateItem(itemId: string, patch: Record<string, unknown>): Promise<SavedItem> {
  return request(`/items/${itemId}`, { method: 'PATCH', body: JSON.stringify(patch) })
}

export async function changeItemStatus(itemId: string, action: 'archive' | 'restore' | 'delete'): Promise<SavedItem> {
  return request(`/items/${itemId}/status?action=${action}`, { method: 'POST' })
}

// --- Revisit / Outcomes ---
export async function getRevisitCandidates(limit = 10): Promise<ResurfacingCandidate[]> {
  return request(`/revisit/candidates?limit=${limit}`)
}

export async function recordOutcome(itemId: string, outcome: OutcomeType, remindAt?: string): Promise<{ item_id: string; lifecycle_state: string }> {
  return request(`/outcomes/${itemId}`, { method: 'POST', body: JSON.stringify({ outcome, remind_at: remindAt }) })
}

// --- Preferences ---
export async function getPreferences(): Promise<UserPreference> {
  return request('/preferences/')
}

export async function updatePreferences(patch: Partial<UserPreference>): Promise<UserPreference> {
  return request('/preferences/', { method: 'PATCH', body: JSON.stringify(patch) })
}

// --- Insights ---
export async function getInsightsSummary(): Promise<InsightsSummary> {
  return request('/insights/summary')
}

// --- Collections ---
export async function listCollections(): Promise<Collection[]> {
  return request('/collections/')
}

export async function createCollection(name: string, description?: string): Promise<Collection> {
  return request('/collections/', { method: 'POST', body: JSON.stringify({ name, description }) })
}

export async function addItemToCollection(collectionId: string, itemId: string): Promise<void> {
  await request(`/collections/${collectionId}/items/${itemId}`, { method: 'POST' })
}

export async function removeItemFromCollection(collectionId: string, itemId: string): Promise<void> {
  await request(`/collections/${collectionId}/items/${itemId}`, { method: 'DELETE' })
}

export async function listCollectionItems(collectionId: string): Promise<string[]> {
  return request(`/collections/${collectionId}/items`)
}

// --- Relationships ---
export async function listRelationshipCandidates(itemId: string): Promise<RelationshipCandidate[]> {
  return request(`/relationships/item/${itemId}/candidates`)
}

export async function listRelationships(itemId: string): Promise<Relationship[]> {
  return request(`/relationships/item/${itemId}`)
}

// --- Feedback ---
export async function recordFeedback(itemId: string, feedbackType: string, selectedValue: string, comment?: string): Promise<Feedback> {
  return request('/feedback/', {
    method: 'POST',
    body: JSON.stringify({ item_id: itemId, feedback_type: feedbackType, selected_value: selectedValue, comment }),
  })
}
