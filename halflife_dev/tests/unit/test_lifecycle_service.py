from datetime import datetime, timedelta
from backend.utils.clock import utcnow
from backend.services.lifecycle_service import LifecycleService
from backend.domain.enums import IntentType, LifecycleState

class MockLifecycleRepo:
    def upsert_assignment(self, assignment):
        return assignment

def test_assign_lifecycle_recipe_with_preferred_day():
    repo = MockLifecycleRepo()
    service = LifecycleService(repo)

    today_name = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][utcnow().weekday()]
    assignment = service.assign_lifecycle(
        "item-123", "user-456", IntentType.RECIPE,
        preferences={"preferred_recipe_days": [today_name]},
    )

    assert assignment.item_id == "item-123"
    assert assignment.current_state == LifecycleState.SCHEDULED_FOR_REVIEW
    assert assignment.next_review_date is not None
    assert "PREFERRED_RECIPE_DAY" in assignment.reason

def test_assign_lifecycle_recipe_without_preference_falls_back_to_manual():
    repo = MockLifecycleRepo()
    service = LifecycleService(repo)

    assignment = service.assign_lifecycle("item-123", "user-456", IntentType.RECIPE, {})

    assert assignment.current_state == LifecycleState.SAVED
    assert assignment.next_review_date is None

def test_assign_lifecycle_general_note():
    repo = MockLifecycleRepo()
    service = LifecycleService(repo)

    assignment = service.assign_lifecycle("item-123", "user-456", IntentType.GENERAL_NOTE, {})

    assert assignment.current_state == LifecycleState.SAVED
    assert assignment.next_review_date is None

def test_assign_lifecycle_task_with_due_date():
    repo = MockLifecycleRepo()
    service = LifecycleService(repo)

    due_at = (utcnow() + timedelta(days=5)).isoformat()
    assignment = service.assign_lifecycle(
        "item-999", "user-456", IntentType.TASK, {},
        intent_attributes={"action_text": "Submit report", "due_at": due_at, "priority": "high", "task_status": "open"},
    )

    assert assignment.current_state == LifecycleState.SCHEDULED_FOR_REVIEW
    assert assignment.next_review_date is not None
    assert "TASK_DUE_SOON" in assignment.reason

def test_assign_lifecycle_activity_log_has_no_scheduled_review():
    repo = MockLifecycleRepo()
    service = LifecycleService(repo)

    assignment = service.assign_lifecycle("item-1", "user-1", IntentType.ACTIVITY_LOG, {})

    assert assignment.current_state == LifecycleState.CLASSIFIED
    assert assignment.next_review_date is None
