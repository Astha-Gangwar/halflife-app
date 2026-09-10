"""Per-intent lifecycle policy functions (Batch 6 §7-§13).

Each function is a pure, deterministic calculation: given the current time,
the item's intent attributes, and the user's preferences, decide the next
lifecycle state and review timing. No policy invents a date it cannot
justify from an explicit input (Batch 6 §21 failure rules) — when a required
input is missing, the item simply falls back to manual-revisit-only.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from backend.utils.clock import utcnow
from typing import Optional, Dict, Any

from backend.domain.enums import LifecycleState
from backend.config.lifecycle_policy_config import (
    WEEKDAY_NAMES,
    LEARNING_MIN_AGE_DAYS,
    IDEA_REVIEW_DAYS_BY_PRIORITY,
    TASK_LEAD_DAYS_BY_PRIORITY,
    TASK_NO_DUE_DATE_REVIEW_DAYS,
    REFERENCE_CATEGORIES,
)


@dataclass
class PolicyResult:
    current_state: LifecycleState
    next_review_date: Optional[datetime]
    eligible_from: Optional[datetime]
    reason: str


def _next_matching_weekday(now: datetime, preferred_days: list) -> Optional[datetime]:
    if not preferred_days:
        return None
    preferred_indices = {WEEKDAY_NAMES.index(d.lower()) for d in preferred_days if d.lower() in WEEKDAY_NAMES}
    if not preferred_indices:
        return None
    for offset in range(0, 8):
        candidate = now + timedelta(days=offset)
        if candidate.weekday() in preferred_indices:
            return candidate
    return None


def recipe_preference_review(now: datetime, intent_attributes: Dict[str, Any], preferences: Dict[str, Any]) -> PolicyResult:
    preferred_days = preferences.get("preferred_recipe_days") or []
    next_day = _next_matching_weekday(now, preferred_days)
    if next_day is not None:
        return PolicyResult(
            current_state=LifecycleState.SCHEDULED_FOR_REVIEW,
            next_review_date=next_day,
            eligible_from=next_day,
            reason="PREFERRED_RECIPE_DAY: scheduled for the next configured recipe-review day.",
        )
    return PolicyResult(
        current_state=LifecycleState.SAVED,
        next_review_date=None,
        eligible_from=None,
        reason="No preferred recipe day configured; eligible only via manual revisit.",
    )


def learning_revisit(now: datetime, intent_attributes: Dict[str, Any], preferences: Dict[str, Any]) -> PolicyResult:
    if intent_attributes.get("completion_percent", 0) >= 100:
        return PolicyResult(
            current_state=LifecycleState.COMPLETED,
            next_review_date=None,
            eligible_from=None,
            reason="Learning content already marked complete; excluded from unread recommendations.",
        )
    eligible_at = now + timedelta(days=LEARNING_MIN_AGE_DAYS)
    return PolicyResult(
        current_state=LifecycleState.SCHEDULED_FOR_REVIEW,
        next_review_date=eligible_at,
        eligible_from=eligible_at,
        reason=f"LEARNING_ITEM_AGED: eligible after the configured {LEARNING_MIN_AGE_DAYS}-day minimum age.",
    )


def idea_development_review(now: datetime, intent_attributes: Dict[str, Any], preferences: Dict[str, Any]) -> PolicyResult:
    maturity = intent_attributes.get("maturity", "captured")
    if maturity in ("defined", "actionable"):
        return PolicyResult(
            current_state=LifecycleState.CLASSIFIED,
            next_review_date=None,
            eligible_from=None,
            reason="Idea has reached a developed maturity stage; no forced inactivity review scheduled.",
        )
    priority = intent_attributes.get("priority", "unspecified")
    window_days = IDEA_REVIEW_DAYS_BY_PRIORITY.get(priority, IDEA_REVIEW_DAYS_BY_PRIORITY["unspecified"])
    eligible_at = now + timedelta(days=window_days)
    return PolicyResult(
        current_state=LifecycleState.SCHEDULED_FOR_REVIEW,
        next_review_date=eligible_at,
        eligible_from=eligible_at,
        reason=f"IDEA_INACTIVE: {priority} priority, eligible after {window_days} day(s) of inactivity.",
    )


def reference_material_review(now: datetime, intent_attributes: Dict[str, Any], preferences: Dict[str, Any]) -> PolicyResult:
    """Checklists, itineraries, and similar reference content: never
    proactively resurfaced on a timer, regardless of intent_type. Retrieved
    only via search, browsing, or an explicit related-memory trigger — this
    is a deliberate choice, not a missing policy, per Batch 6's "don't
    decay content that was never time-bound" principle."""
    return PolicyResult(
        current_state=LifecycleState.SAVED,
        next_review_date=None,
        eligible_from=None,
        reason="REFERENCE_CATEGORY: reference material is not proactively resurfaced; retrievable via search or browsing only.",
    )


def task_due_date_review(now: datetime, intent_attributes: Dict[str, Any], preferences: Dict[str, Any]) -> PolicyResult:
    task_status = intent_attributes.get("task_status", "open")
    if task_status in ("completed", "cancelled"):
        return PolicyResult(
            current_state=LifecycleState.COMPLETED if task_status == "completed" else LifecycleState.NOT_RELEVANT,
            next_review_date=None,
            eligible_from=None,
            reason=f"Task status is {task_status}; excluded from open-task resurfacing.",
        )

    due_at_raw = intent_attributes.get("due_at")
    priority = intent_attributes.get("priority", "unspecified")
    lead_days = TASK_LEAD_DAYS_BY_PRIORITY.get(priority, TASK_LEAD_DAYS_BY_PRIORITY["unspecified"])

    if due_at_raw:
        try:
            due_at = due_at_raw if isinstance(due_at_raw, datetime) else datetime.fromisoformat(str(due_at_raw))
        except ValueError:
            # The agent is instructed to only ever store a resolved ISO date
            # under due_at, never a raw phrase like "tomorrow" — but an LLM
            # occasionally not following that instruction must not crash the
            # whole capture. Fall back the same as "no due date at all,"
            # with a reason that makes the bad value visible for debugging
            # rather than silently swallowing it.
            eligible_at = now + timedelta(days=TASK_NO_DUE_DATE_REVIEW_DAYS)
            return PolicyResult(
                current_state=LifecycleState.SCHEDULED_FOR_REVIEW,
                next_review_date=eligible_at,
                eligible_from=eligible_at,
                reason=(
                    f"UNRESOLVABLE_DUE_DATE: due_at was set but not a valid ISO date "
                    f"({due_at_raw!r}); falling back to the {TASK_NO_DUE_DATE_REVIEW_DAYS}-day age-based review rule."
                ),
            )
        eligible_at = due_at - timedelta(days=lead_days)
        reason_code = "TASK_OVERDUE" if due_at < now else "TASK_DUE_SOON"
        return PolicyResult(
            current_state=LifecycleState.SCHEDULED_FOR_REVIEW,
            next_review_date=eligible_at,
            eligible_from=eligible_at,
            reason=f"{reason_code}: due at {due_at.isoformat()}, lead window {lead_days} day(s).",
        )

    eligible_at = now + timedelta(days=TASK_NO_DUE_DATE_REVIEW_DAYS)
    return PolicyResult(
        current_state=LifecycleState.SCHEDULED_FOR_REVIEW,
        next_review_date=eligible_at,
        eligible_from=eligible_at,
        reason=f"No resolved due date; falling back to the {TASK_NO_DUE_DATE_REVIEW_DAYS}-day age-based review rule.",
    )


def activity_comparison(now: datetime, intent_attributes: Dict[str, Any], preferences: Dict[str, Any]) -> PolicyResult:
    return PolicyResult(
        current_state=LifecycleState.CLASSIFIED,
        next_review_date=None,
        eligible_from=None,
        reason="Activity logs are not scheduled for reminder treatment; they participate in comparison only.",
    )


def semantic_context_review(now: datetime, intent_attributes: Dict[str, Any], preferences: Dict[str, Any]) -> PolicyResult:
    return PolicyResult(
        current_state=LifecycleState.SAVED,
        next_review_date=None,
        eligible_from=None,
        reason="General notes are eligible only via manual revisit or a related-memory context trigger.",
    )


POLICY_DISPATCH = {
    "recipe": recipe_preference_review,
    "learning_content": learning_revisit,
    "idea": idea_development_review,
    "task": task_due_date_review,
    "activity_log": activity_comparison,
    "general_note": semantic_context_review,
}


def evaluate_policy(
    intent_value: str,
    now: datetime,
    intent_attributes: Dict[str, Any],
    preferences: Dict[str, Any],
    category: Optional[str] = None,
) -> PolicyResult:
    # Category-based reference override takes priority over the per-intent
    # dispatch below: a checklist or itinerary saved as an idea or a note is
    # still reference material, not a reminder, regardless of intent_type.
    if category and category.strip().lower() in REFERENCE_CATEGORIES:
        return reference_material_review(now, intent_attributes or {}, preferences or {})

    policy_fn = POLICY_DISPATCH.get(intent_value)
    if policy_fn is None:
        return PolicyResult(
            current_state=LifecycleState.SAVED,
            next_review_date=None,
            eligible_from=None,
            reason=f"No lifecycle policy defined for intent '{intent_value}'.",
        )
    return policy_fn(now, intent_attributes or {}, preferences or {})
