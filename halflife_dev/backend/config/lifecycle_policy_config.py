"""Configuration values for the MVP lifecycle/resurfacing policies (Batch 6).

These are explicit, versioned, tunable values — not learned parameters.
Per Batch 6 §11.2 "Configurable default": exact intervals are configuration
values to be tested with users, not hardcoded product truths.
"""

POLICY_VERSION = "v1.0"

WEEKDAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# Generic dismissal cooldown per intent (days), used when the user dismisses
# a presented item without an explicit "remind me on X" date. Batch 6 §17.
DEFAULT_COOLDOWN_DAYS = {
    "recipe": 3,
    "learning_content": 3,
    "idea": 7,
    "task": 1,
    "activity_log": 3,
    "general_note": 14,
}

# Minimum age (days) before an incomplete learning item becomes eligible. Batch 6 §9.1.
LEARNING_MIN_AGE_DAYS = 3

# Inactivity window (days) before an undeveloped idea becomes eligible. Batch 6 §10.1.
# Kept as the "unspecified" fallback below for backward compatibility.
IDEA_INACTIVITY_WINDOW_DAYS = 14

# Inactivity window (days) before an undeveloped idea becomes eligible, scaled
# by the same priority the user gave it (or "unspecified" if never asked).
# Mirrors TASK_LEAD_DAYS_BY_PRIORITY's shape: priority scales cadence within
# the "someday" bucket, it does not decide whether an item is in that bucket.
IDEA_REVIEW_DAYS_BY_PRIORITY = {
    "high": 7,
    "medium": 14,
    "low": 30,
    "unspecified": IDEA_INACTIVITY_WINDOW_DAYS,
}

# Categories that mean "reference material, not a reminder" regardless of
# which intent_type the content was classified as (a checklist or travel
# itinerary saved as a general_note, an idea, or anything else). These are
# never proactively resurfaced on a timer — retrievable only by search,
# browsing, or an explicit "related memories" trigger. Matched against
# SavedItem.category, case-insensitive, after stripping whitespace.
REFERENCE_CATEGORIES = {
    "checklist",
    "reference",
    "itinerary",
    "travel itinerary",
    "travel checklist",
    "packing list",
}

# Lead window (days) before a task's due date that it becomes eligible, by priority. Batch 6 §11.2.
TASK_LEAD_DAYS_BY_PRIORITY = {
    "high": 3,
    "medium": 1,
    "low": 0,
    "unspecified": 1,
}

# Fallback age-based review window (days) for an open task with no resolved due date. Batch 6 §11.1.
TASK_NO_DUE_DATE_REVIEW_DAYS = 30

# Default revisit-candidate ranking weights (Batch 6 §15). Higher = more important.
RANKING_WEIGHTS = {
    "explicit_due_or_requested_date": 100,
    "policy_eligibility": 50,
    "age_since_save_or_action": 10,
    "related_current_context": 20,
    "effort_preference_fit": 15,
    "previous_positive_feedback": 5,
    "recent_resurfacing": -50,
    "dismissal_count": -20,
}

# Maximum items returned per revisit request unless the caller asks for fewer. Batch 6 §14.
DEFAULT_REVISIT_LIMIT = 10
