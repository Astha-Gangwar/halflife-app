from datetime import datetime, timedelta
from backend.utils.clock import utcnow
from backend.services.lifecycle_policies import evaluate_policy
from backend.domain.enums import LifecycleState


def test_learning_content_completed_excludes_from_reminders():
    now = utcnow()
    result = evaluate_policy("learning_content", now, {"completion_percent": 100}, {})
    assert result.current_state == LifecycleState.COMPLETED
    assert result.next_review_date is None


def test_learning_content_incomplete_gets_aged_review():
    now = utcnow()
    result = evaluate_policy("learning_content", now, {"completion_percent": 0}, {})
    assert result.current_state == LifecycleState.SCHEDULED_FOR_REVIEW
    assert result.next_review_date > now


def test_idea_captured_gets_inactivity_review():
    now = utcnow()
    result = evaluate_policy("idea", now, {"maturity": "captured"}, {})
    assert result.current_state == LifecycleState.SCHEDULED_FOR_REVIEW
    assert result.next_review_date is not None


def test_idea_actionable_has_no_forced_review():
    now = utcnow()
    result = evaluate_policy("idea", now, {"maturity": "actionable"}, {})
    assert result.current_state == LifecycleState.CLASSIFIED
    assert result.next_review_date is None


def test_idea_high_priority_resurfaces_sooner_than_low_priority():
    now = utcnow()
    high = evaluate_policy("idea", now, {"maturity": "captured", "priority": "high"}, {})
    low = evaluate_policy("idea", now, {"maturity": "captured", "priority": "low"}, {})
    assert high.next_review_date < low.next_review_date


def test_idea_unspecified_priority_matches_legacy_default_window():
    now = utcnow()
    result = evaluate_policy("idea", now, {"maturity": "captured"}, {})
    assert result.current_state == LifecycleState.SCHEDULED_FOR_REVIEW
    delta_days = (result.next_review_date - now).days
    assert delta_days == 14


def test_task_completed_is_excluded():
    now = utcnow()
    result = evaluate_policy("task", now, {"task_status": "completed"}, {})
    assert result.current_state == LifecycleState.COMPLETED
    assert result.next_review_date is None


def test_task_overdue_gets_flagged():
    now = utcnow()
    past_due = (now - timedelta(days=2)).isoformat()
    result = evaluate_policy("task", now, {"task_status": "open", "due_at": past_due, "priority": "medium"}, {})
    assert result.current_state == LifecycleState.SCHEDULED_FOR_REVIEW
    assert "TASK_OVERDUE" in result.reason


def test_task_without_due_date_falls_back_to_age_review():
    now = utcnow()
    result = evaluate_policy("task", now, {"task_status": "open"}, {})
    assert result.current_state == LifecycleState.SCHEDULED_FOR_REVIEW
    assert result.next_review_date > now + timedelta(days=20)


def test_task_with_unparseable_due_at_falls_back_safely_instead_of_crashing():
    """Regression test: if the agent ever stores a raw relative phrase like
    "tomorrow" under due_at instead of a resolved ISO date, the policy must
    not raise — it should fall back the same as no due date at all, with a
    reason that makes the bad value visible rather than a silent crash."""
    now = utcnow()
    result = evaluate_policy("task", now, {"task_status": "open", "due_at": "tomorrow"}, {})
    assert result.current_state == LifecycleState.SCHEDULED_FOR_REVIEW
    assert "UNRESOLVABLE_DUE_DATE" in result.reason
    assert "tomorrow" in result.reason
    assert result.next_review_date > now + timedelta(days=20)


def test_general_note_is_manual_revisit_only():
    now = utcnow()
    result = evaluate_policy("general_note", now, {}, {})
    assert result.current_state == LifecycleState.SAVED
    assert result.next_review_date is None


def test_unknown_intent_falls_back_safely():
    now = utcnow()
    result = evaluate_policy("unknown", now, {}, {})
    assert result.current_state == LifecycleState.SAVED
    assert result.next_review_date is None


def test_checklist_category_overrides_task_due_date_policy():
    now = utcnow()
    soon = (now + timedelta(days=1)).isoformat()
    result = evaluate_policy(
        "task", now,
        {"task_status": "open", "due_at": soon, "priority": "high"},
        {},
        category="checklist",
    )
    assert result.current_state == LifecycleState.SAVED
    assert result.next_review_date is None
    assert "REFERENCE_CATEGORY" in result.reason


def test_reference_category_is_case_and_whitespace_insensitive():
    now = utcnow()
    result = evaluate_policy("idea", now, {"maturity": "captured"}, {}, category="  Travel Itinerary  ")
    assert result.current_state == LifecycleState.SAVED
    assert result.next_review_date is None


def test_ordinary_category_does_not_trigger_reference_override():
    now = utcnow()
    result = evaluate_policy("idea", now, {"maturity": "captured"}, {}, category="product-ideas")
    assert result.current_state == LifecycleState.SCHEDULED_FOR_REVIEW
