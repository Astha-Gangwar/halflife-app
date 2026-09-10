import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { captureContent, confirmCapture, type CaptureResponse } from '../services/api'
import { useAuth } from '../hooks/useAuth'

// Most captures need a second "does this look right?" confirmation before
// anything is actually saved (see handleConfirm) -- the agent has no memory
// of the first turn, so that pending state only exists in this component.
// Home (and this component with it) unmounts on every navigation, which
// used to destroy that state outright: click Capture, click a nav link
// before confirming, and the capture was gone with no warning. Persisting
// it here means navigating away and back still shows the same pending
// confirmation instead of silently losing it.
const PENDING_KEY = 'halflife_pending_capture'

interface PendingState {
  pendingContent: string
  result: CaptureResponse
  correctionNote: string
}

function loadPending(): PendingState | null {
  try {
    const raw = sessionStorage.getItem(PENDING_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function savePending(state: PendingState | null) {
  try {
    if (state) sessionStorage.setItem(PENDING_KEY, JSON.stringify(state))
    else sessionStorage.removeItem(PENDING_KEY)
  } catch {
    // sessionStorage unavailable (private mode etc.) -- the in-memory
    // state still works for as long as the component stays mounted
  }
}

const CaptureInput: React.FC = () => {
  const { isDemo } = useAuth()
  const initialPending = loadPending()
  const [content, setContent] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [result, setResult] = useState<CaptureResponse | null>(initialPending?.result ?? null)
  const [pendingContent, setPendingContent] = useState<string | null>(initialPending?.pendingContent ?? null)
  const [correctionNote, setCorrectionNote] = useState(initialPending?.correctionNote ?? '')
  const [error, setError] = useState<string | null>(null)

  if (isDemo) {
    return (
      <div className="glass-panel" style={{ padding: '32px', maxWidth: '800px', margin: '0 auto', animationDelay: '0.1s' }}>
        <h3 style={{ marginBottom: '16px', fontSize: '1.5rem' }}>What's on your mind?</h3>
        <p style={{ color: 'var(--text-secondary)' }}>
          Capturing new memories is disabled in the demo account — sign in with your own account to try it.
        </p>
      </div>
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!content.trim()) return

    setIsSubmitting(true)
    setError(null)
    setResult(null)
    try {
      const idempotencyKey = crypto.randomUUID()
      const submitted = content.trim()
      const response = await captureContent(submitted, idempotencyKey)
      setResult(response)
      const stillPending = response.item_created ? null : submitted
      setPendingContent(stillPending)
      savePending(stillPending ? { pendingContent: stillPending, result: response, correctionNote: '' } : null)
      setContent('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Capture failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleConfirm = async (accept: boolean) => {
    if (!pendingContent) return
    if (!accept) {
      setPendingContent(null)
      setCorrectionNote('')
      setResult(null)
      savePending(null)
      return
    }
    setIsSubmitting(true)
    setError(null)
    try {
      const corrections = correctionNote.trim() ? { note: correctionNote.trim() } : undefined
      const response = await confirmCapture(pendingContent, corrections)
      setResult(response)
      const stillPending = response.item_created ? null : pendingContent
      setPendingContent(stillPending)
      // If the agent needs another round instead of saving, the correction
      // just given must carry forward -- every confirm call resends the
      // ORIGINAL content (the agent has no memory between turns), so
      // clearing this unconditionally meant a second round silently dropped
      // the user's correction and the next save reverted to a fresh,
      // uncorrected classification of the ambiguous original text.
      const carriedNote = stillPending ? correctionNote : ''
      savePending(stillPending ? { pendingContent: stillPending, result: response, correctionNote: carriedNote } : null)
      setCorrectionNote(carriedNote)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Confirm failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="glass-panel" style={{ padding: '32px', maxWidth: '800px', margin: '0 auto', animationDelay: '0.1s' }}>
      <h3 style={{ marginBottom: '16px', fontSize: '1.5rem' }}>What's on your mind?</h3>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
        Paste a recipe, note down a task, or log an activity. I'll figure out how to organize it.
      </p>

      <form onSubmit={handleSubmit}>
        <textarea
          className="input-base"
          style={{ minHeight: '120px', resize: 'vertical', marginBottom: '16px', fontSize: '1.1rem' }}
          placeholder="e.g., I want to try making sourdough bread this weekend. Or: Need to renew my passport."
          value={content}
          onChange={(e) => setContent(e.target.value)}
          disabled={isSubmitting}
        />

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button type="submit" className="btn-primary" disabled={isSubmitting || !content.trim()}>
            {isSubmitting ? 'Analyzing...' : 'Capture Memory'}
            {!isSubmitting && (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            )}
          </button>
        </div>
      </form>

      {result && (
        <div style={{ marginTop: '20px', padding: '16px', borderRadius: '8px', background: 'rgba(0, 212, 255, 0.08)', border: '1px solid var(--border-color)' }}>
          <div className="markdown-body">
            <ReactMarkdown>{result.message}</ReactMarkdown>
          </div>

          {result.item_created ? (
            <p style={{ marginTop: '12px', marginBottom: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              ✓ Saved.
            </p>
          ) : result.is_refusal ? (
            // A flat refusal isn't a proposed classification waiting on your
            // OK -- there's nothing to confirm or correct, so don't offer
            // "Looks Good, Save It" here. Dismissing just clears the pending
            // state the same way Cancel does below.
            <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end' }}>
              <button type="button" className="btn-secondary" onClick={() => handleConfirm(false)}>
                OK
              </button>
            </div>
          ) : pendingContent && (
            <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--border-color)' }}>
              <p style={{ marginBottom: '10px', fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
                This hasn't been saved yet — confirm it looks right, or add a correction first.
              </p>
              <textarea
                className="input-base"
                style={{ minHeight: '60px', resize: 'vertical', marginBottom: '12px', fontSize: '1rem' }}
                placeholder="Optional: describe a correction (e.g. 'make it a task due Friday')"
                value={correctionNote}
                onChange={(e) => {
                  setCorrectionNote(e.target.value)
                  savePending({ pendingContent, result, correctionNote: e.target.value })
                }}
                disabled={isSubmitting}
              />
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button type="button" className="btn-secondary" onClick={() => handleConfirm(false)} disabled={isSubmitting}>
                  Cancel
                </button>
                <button type="button" className="btn-primary" onClick={() => handleConfirm(true)} disabled={isSubmitting}>
                  {isSubmitting ? 'Saving...' : correctionNote.trim() ? 'Apply Correction & Save' : 'Looks Good, Save It'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
      {error && (
        <div style={{ marginTop: '20px', padding: '16px', borderRadius: '8px', background: 'rgba(255, 107, 107, 0.08)', border: '1px solid var(--border-color)', color: '#ff6b6b' }}>
          {error}
        </div>
      )}
    </div>
  )
}

export default CaptureInput
