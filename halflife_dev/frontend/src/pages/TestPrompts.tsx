import React, { useState } from 'react'

interface Scenario {
  title: string
  chip: string
  chipClass: string
  prompt: string
  expect: string
  check: string
}

const STRAIGHT_THROUGH: Scenario[] = [
  {
    title: 'Due-dated task',
    chip: 'Task',
    chipClass: 'chip-blue',
    prompt: 'Renew my passport before it expires on October 15',
    expect: 'Relative date resolved to a real due date; saved immediately, no confirmation.',
    check: 'Library — "Task" chip, category "admin"',
  },
  {
    title: 'Recipe with ingredients',
    chip: 'Recipe',
    chipClass: 'chip-amber',
    prompt:
      'Recipe for garlic butter shrimp pasta: shrimp, garlic, butter, chili flakes, linguine, parsley. Cook the pasta, saute garlic in butter, toss in shrimp, combine with pasta.',
    expect: 'Ingredients extracted into structured fields, category "cooking". May ask a quick confirmation first — that\'s the agent working as intended, not a bug.',
    check: 'Library — "Recipe" chip; resurfaces on your preferred recipe day',
  },
  {
    title: 'Idea, no deadline',
    chip: 'Idea',
    chipClass: 'chip-purple',
    prompt: 'Idea: build a browser extension that mutes autoplay videos automatically',
    expect: 'Saved as an idea, category "product-ideas" — no due date asked for.',
    check: 'Library — "Idea" chip; ages and resurfaces if left untouched',
  },
  {
    title: 'Activity log',
    chip: 'Activity',
    chipClass: 'chip-green',
    prompt: 'Ran 5k this morning in 27 minutes, felt strong',
    expect: 'Logged as a past event, category "fitness" — this type doesn\'t resurface.',
    check: 'Library — "Activity Log" chip',
  },
  {
    title: 'General note',
    chip: 'Note',
    chipClass: 'chip-gray',
    prompt: 'Wifi password for the new router is on a sticky note inside the hallway cabinet',
    expect: 'Saved as a plain note, category "home". May ask what to title it first.',
    check: 'Library — "Note" chip',
  },
  {
    title: 'Reference / checklist',
    chip: 'Reference',
    chipClass: 'chip-red',
    prompt: 'Packing list for the Goa trip: passport, chargers, sunscreen, swimwear, flip-flops, power bank',
    expect: 'Saved, but deliberately kept dormant — reference content is never pushed back at you.',
    check: 'Library search "packing" — should never appear on Revisit, even if old',
  },
]

const RELATED_ITEMS: Scenario[] = [
  {
    title: 'First item',
    chip: 'Task',
    chipClass: 'chip-blue',
    prompt: 'Try making sourdough bread this weekend',
    expect: 'Capture this one first.',
    check: '',
  },
  {
    title: 'Second item',
    chip: 'Recipe',
    chipClass: 'chip-amber',
    prompt: 'Recipe for classic Neapolitan pizza dough: flour, water, salt, yeast. Knead, proof 24 hours, stretch by hand.',
    expect: 'Both land in category "cooking" — close enough to be linked.',
    check: 'Item detail — "Related memories" lists the other item',
  },
]

const CHEATSHEET: { behavior: string; visible: string; screen: string }[] = [
  { behavior: 'Confident classification', visible: 'Item saved immediately, confirmation message in chat', screen: 'Today (capture result) → Library' },
  { behavior: 'Ambiguous content', visible: '"This hasn\'t been saved yet" panel, Cancel / Save buttons', screen: 'Today — persists across navigation' },
  { behavior: 'Correction applied', visible: 'Re-classified item, correction note discarded after save', screen: 'Today → Library' },
  { behavior: 'Outcome recorded', visible: 'Colored lifecycle-state label, "Complete" button hidden', screen: 'Library row, Item Detail' },
  { behavior: 'Related content detected', visible: 'Candidate listed with a shared-context reason', screen: 'Item Detail → "Related memories"' },
  { behavior: 'Saving behavior over time', visible: 'Consumption rate, active/stale backlog, category performance', screen: 'Insights' },
  { behavior: 'Grouped by topic', visible: 'Real per-collection item counts and acted-on rate', screen: 'Collections, Collection Detail' },
  { behavior: 'Due/aging content', visible: 'Only what\'s eligible right now, with a plain-language reason', screen: 'Revisit' },
]

const PromptBlock: React.FC<{ text: string }> = ({ text }) => {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      // clipboard API unavailable -- selection still shows the text below
    }
    setCopied(true)
    setTimeout(() => setCopied(false), 1300)
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={copy}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); copy() } }}
      style={{
        background: 'rgba(0, 0, 0, 0.35)',
        border: `1px solid ${copied ? 'var(--status-green)' : 'var(--border-color)'}`,
        borderRadius: '8px',
        padding: '10px 36px 10px 12px',
        cursor: 'pointer',
        fontFamily: 'ui-monospace, "SF Mono", Consolas, monospace',
        fontSize: '0.82rem',
        lineHeight: 1.5,
        color: 'var(--text-primary)',
        position: 'relative',
      }}
    >
      {text}
      <span
        style={{
          position: 'absolute', top: '8px', right: '10px',
          fontSize: '0.75rem', color: copied ? 'var(--status-green)' : 'var(--text-secondary)',
        }}
      >
        {copied ? '✓ Copied' : '⧉ Copy'}
      </span>
    </div>
  )
}

const ScenarioCard: React.FC<{ s: Scenario }> = ({ s }) => (
  <div className="glass-panel" style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ fontWeight: 600 }}>{s.title}</span>
      <span className={`chip ${s.chipClass}`}>{s.chip}</span>
    </div>
    <PromptBlock text={s.prompt} />
    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
      <div><b style={{ color: 'var(--text-primary)' }}>Expect:</b> {s.expect}</div>
      {s.check && <div><b style={{ color: 'var(--text-primary)' }}>Check:</b> {s.check}</div>}
    </div>
  </div>
)

const SectionHeading: React.FC<{ num: string; title: string; sub: string }> = ({ num, title, sub }) => (
  <div style={{ marginBottom: '18px' }}>
    <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}>
      <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: '0.8rem', color: 'var(--secondary-color)' }}>{num}</span>
      <h3 style={{ margin: 0, fontSize: '1.2rem' }}>{title}</h3>
    </div>
    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '6px', marginBottom: 0, maxWidth: '70ch' }}>{sub}</p>
  </div>
)

const TestPrompts: React.FC = () => {
  return (
    <main className="container" style={{ paddingBottom: '80px' }}>
      <div style={{ marginBottom: '32px' }}>
        <h2 style={{ fontSize: '2.2rem', marginBottom: '8px' }}>Capture Test Playbook</h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '70ch' }}>
          A copyable set of things to type into the capture box above, chosen to exercise every
          path the agent can take — clean saves, clarifying questions, corrections, related-item
          detection, and the lifecycle/outcome loop. Click any prompt block to copy it, paste it
          into the "What's on your mind?" box on the Today page, and compare against Expect.
        </p>
      </div>

      <section style={{ marginBottom: '48px' }}>
        <SectionHeading
          num="01"
          title="Straight-through captures"
          sub="Each of these is unambiguous enough that the agent should usually save it on the first try — one per supported content type."
        />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
          {STRAIGHT_THROUGH.map((s) => <ScenarioCard key={s.title} s={s} />)}
        </div>
      </section>

      <section style={{ marginBottom: '48px' }}>
        <SectionHeading
          num="02"
          title="Confirmation & correction loop"
          sub="When content is genuinely ambiguous, the agent asks a focused question instead of guessing — nothing is saved until you respond."
        />
        <div style={{ display: 'grid', gap: '16px' }}>
          <div className="glass-panel" style={{ padding: '18px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span style={{ fontWeight: 600 }}>Under-specified capture → clarifying question</span>
              <span className="chip chip-purple">Confirmation loop</span>
            </div>
            <PromptBlock text="Sourdough starter" />
            <ol style={{ marginTop: '14px', paddingLeft: '20px', color: 'var(--text-secondary)', fontSize: '0.88rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <li>Submit and read the clarifying question (e.g. "Is this a recipe, or a reminder to feed a starter you already have?")</li>
              <li>The capture box switches to a pending panel — nothing is saved yet. Reload or navigate away: it survives.</li>
              <li>Type a correction ("It's a recipe") or click Cancel to discard.</li>
              <li>Once accepted, the item saves — check Library for the corrected type.</li>
            </ol>
          </div>
          <div className="glass-panel" style={{ padding: '18px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span style={{ fontWeight: 600 }}>Vague capture → correction changes the outcome</span>
              <span className="chip chip-purple">Correction loop</span>
            </div>
            <PromptBlock text="Something about the tax thing" />
            <p style={{ margin: '12px 0 6px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Then, in the correction box:</p>
            <PromptBlock text="It's a task: file taxes, due April 15" />
            <p style={{ marginTop: '10px', marginBottom: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              <b style={{ color: 'var(--text-primary)' }}>Expect:</b> Library shows a Task "file taxes", category admin, due April 15 — reflecting the correction, not the vague original text.
            </p>
          </div>
        </div>
      </section>

      <section style={{ marginBottom: '48px' }}>
        <SectionHeading
          num="03"
          title="Related-item detection"
          sub="Capturing two items sharing a category, content type, or tag should surface each as a relationship candidate on the other's detail page."
        />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
          {RELATED_ITEMS.map((s) => <ScenarioCard key={s.title} s={s} />)}
        </div>
      </section>

      <section style={{ marginBottom: '48px' }}>
        <SectionHeading
          num="04"
          title="Outcomes & lifecycle state"
          sub="This one's a UI action, not a capture — there's nothing to paste."
        />
        <div className="glass-panel" style={{ padding: '18px' }}>
          <ol style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.9rem' }}>
            <li>Open any saved item's detail page and click <b>Tried it</b>, <b>Completed</b>, or <b>Not relevant</b> under "Record an outcome".</li>
            <li>The item's state updates immediately, in place — no reload needed.</li>
            <li>Back on Library: that row now shows a colored lifecycle label instead of the "Complete" button.</li>
            <li>On Insights: Consumption Rate and that item's category row reflect the outcome.</li>
          </ol>
        </div>
      </section>

      <section style={{ marginBottom: '48px' }}>
        <SectionHeading
          num="05"
          title="Collections"
          sub="Also a UI action — creating a collection is the testable path today."
        />
        <div className="glass-panel" style={{ padding: '18px' }}>
          <ol style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.9rem' }}>
            <li>On the Collections page, create one named anything (e.g. "Cooking").</li>
            <li>Its card should show <b>real</b> counts — 0 items, 0% acted on, "No activity yet" — for a brand-new, empty collection.</li>
            <li>Open the collection: the KPI strip should match the card exactly.</li>
          </ol>
        </div>
      </section>

      <section>
        <SectionHeading
          num="06"
          title="Where it shows up"
          sub="A quick lookup for what a given agent behavior should produce, and on which screen."
        />
        <div className="glass-panel" style={{ padding: '0', overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', minWidth: '640px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <th style={{ textAlign: 'left', padding: '12px 16px', color: 'var(--text-secondary)' }}>Agent behavior</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', color: 'var(--text-secondary)' }}>Visible as</th>
                  <th style={{ textAlign: 'left', padding: '12px 16px', color: 'var(--text-secondary)' }}>Screen</th>
                </tr>
              </thead>
              <tbody>
                {CHEATSHEET.map((row) => (
                  <tr key={row.behavior} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 600 }}>{row.behavior}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{row.visible}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{row.screen}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </main>
  )
}

export default TestPrompts
