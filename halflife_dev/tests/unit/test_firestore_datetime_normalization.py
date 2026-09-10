"""Regression test for the real production bug: ResurfacingService.
get_revisit_candidates raised "can't compare offset-naive and
offset-aware datetimes" against real Firestore, because Firestore's
client returns timezone-aware datetimes on read regardless of how they
were stored. mock-firestore (this project's test fake) doesn't replicate
that specific behavior, so this test manually writes a document with a
timezone-aware `next_review_date` directly into the fake — reproducing
exactly what a read from real Firestore actually looks like — rather than
going through the repository's own write path, which would just store
back whatever naive value it was given.
"""
from datetime import datetime, timedelta, timezone
from backend.repositories.firestore.firestore_lifecycle_repository import FirestoreLifecycleRepository
from backend.repositories.firestore.firestore_resurfacing_repository import FirestoreResurfacingRepository
from backend.services.resurfacing_service import ResurfacingService
from backend.domain.enums import LifecycleState


def test_revisit_candidates_does_not_crash_on_timezone_aware_data_from_firestore(db_session):
    aware_past_due = datetime.now(timezone.utc) - timedelta(days=1)

    db_session.collection("lifecycle_assignments").document("assign-1").set({
        "assignment_id": "assign-1",
        "user_id": "user-1",
        "item_id": "item-1",
        "policy_id": "task_policy",
        "policy_version": "v1.0",
        "current_state": LifecycleState.SCHEDULED_FOR_REVIEW.value,
        "next_review_date": aware_past_due,  # timezone-aware, as real Firestore returns
        "eligible_from": aware_past_due,
        "cooldown_until": None,
        "reason": "TASK_OVERDUE: due yesterday",
        "created_at": aware_past_due,
        "updated_at": aware_past_due,
        "version": 1,
    })

    service = ResurfacingService(
        FirestoreLifecycleRepository(db_session),
        FirestoreResurfacingRepository(db_session),
    )

    # This is the exact line that raised TypeError against real Firestore
    # (resurfacing_service.py: `assignment.next_review_date > now`, where
    # `now` is a naive utcnow()) before the fix.
    candidates = service.get_revisit_candidates("user-1")

    assert len(candidates) == 1
    assert candidates[0].item_id == "item-1"
