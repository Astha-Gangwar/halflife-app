export type IntentType =
  | 'recipe' | 'learning_content' | 'idea' | 'task' | 'activity_log' | 'general_note' | 'unknown'

export type ItemStatus = 'draft' | 'active' | 'archived' | 'deleted'

export type LifecycleState =
  | 'saved' | 'classified' | 'grouped' | 'scheduled_for_review' | 'resurfaced'
  | 'tried' | 'modified' | 'completed' | 'dismissed' | 'not_relevant' | 'archived'

export type OutcomeType =
  | 'tried' | 'completed' | 'modified' | 'remind_later' | 'dismissed'
  | 'not_relevant' | 'archived' | 'restored'

// current_lifecycle_state values that mean "the user has already recorded an
// outcome on this item" versus it still sitting untouched in the backlog.
// Mirrors backend/services/insights_service.py's ACTED_ON_STATES.
export const ACTED_ON_STATES: ReadonlySet<LifecycleState> = new Set([
  'tried', 'completed', 'dismissed', 'not_relevant', 'modified',
])

export interface SavedItem {
  item_id: string
  user_id: string
  original_content: string
  content_format: string
  user_title?: string | null
  user_note?: string | null
  approved_title: string
  approved_summary?: string | null
  intent_type: IntentType
  category?: string | null
  tags: string[]
  intent_attributes: Record<string, unknown>
  approved_analysis_id: string
  status: ItemStatus
  current_lifecycle_state: LifecycleState
  version: number
  created_at: string
  updated_at: string
  archived_at?: string | null
  deleted_at?: string | null
}

export interface ResurfacingCandidate {
  resurfacing_id: string
  user_id: string
  item_id: string
  assignment_id: string
  status: string
  eligibility_reason_code: string
  supporting_facts: Record<string, unknown>
  rank_score?: number | null
  rank_factors: Record<string, unknown>
  eligible_at: string
}

export interface UserPreference {
  preference_id: string
  user_id: string
  timezone: string
  preferred_recipe_days: string[]
  preferred_review_period?: string | null
  max_recipe_effort_minutes?: number | null
  max_learning_effort_minutes?: number | null
  revisit_frequency_limit?: number | null
  uncertain_item_handling: string
  version: number
}

export interface Collection {
  collection_id: string
  user_id: string
  name: string
  description?: string | null
  status: string
  version: number
}

export interface Relationship {
  relationship_id: string
  source_item_id: string
  target_item_id: string
  relationship_type: string
  reason: string
  status: string
}

export interface RelationshipCandidate {
  candidate_id: string
  source_item_id: string
  target_item_id: string
  suggested_type: string
  similarity_score?: number | null
  supporting_facts: string[]
  status: string
}

export interface Feedback {
  feedback_id: string
  item_id: string
  feedback_type: string
  selected_value: string
  comment?: string | null
  submitted_at: string
}

export interface CategoryPerformance {
  category: string
  total: number
  acted_on_rate: number
}

export interface InsightsSummary {
  total_saved: number
  consumption_rate: number
  active_backlog: number
  stale_backlog: number
  stale_backlog_rate: number
  revisit_success_rate: number | null
  category_performance: CategoryPerformance[]
  behavior_insights: string[]
}

export const INTENT_LABELS: Record<IntentType, string> = {
  recipe: 'Recipe',
  learning_content: 'Learning',
  idea: 'Idea',
  task: 'Task',
  activity_log: 'Activity',
  general_note: 'Note',
  unknown: 'Unknown',
}
