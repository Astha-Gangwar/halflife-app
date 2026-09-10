from datetime import datetime, timedelta
from backend.utils.clock import utcnow
from backend.services.resurfacing_service import ResurfacingService
from backend.repositories.firestore.firestore_lifecycle_repository import FirestoreLifecycleRepository
from backend.repositories.firestore.firestore_resurfacing_repository import FirestoreResurfacingRepository
from backend.domain.schemas.lifecycle import LifecycleAssignment
from backend.domain.enums import LifecycleState, ResurfacingStatus


def _past_due_assignment(item_id, user_id="user-1"):
    now = utcnow()
    return LifecycleAssignment(
        assignment_id=f"assign-{item_id}",
        user_id=user_id,
        item_id=item_id,
        policy_version="v1.0",
        current_state=LifecycleState.SCHEDULED_FOR_REVIEW,
        next_review_date=now - timedelta(days=1),
        eligible_from=now - timedelta(days=1),
        reason="TASK_OVERDUE: due yesterday",
    )


def test_get_revisit_candidates_excludes_future_and_cooldown(db_session):
    lifecycle_repo = FirestoreLifecycleRepository(db_session)
    resurfacing_repo = FirestoreResurfacingRepository(db_session)
    service = ResurfacingService(lifecycle_repo, resurfacing_repo)

    lifecycle_repo.upsert_assignment(_past_due_assignment("item-due"))

    future = _past_due_assignment("item-future")
    future.next_review_date = utcnow() + timedelta(days=5)
    lifecycle_repo.upsert_assignment(future)

    in_cooldown = _past_due_assignment("item-cooldown")
    in_cooldown.cooldown_until = utcnow() + timedelta(days=1)
    lifecycle_repo.upsert_assignment(in_cooldown)

    candidates = service.get_revisit_candidates("user-1")
    item_ids = {c.item_id for c in candidates}
    assert item_ids == {"item-due"}
    assert candidates[0].eligibility_reason_code == "TASK_OVERDUE"
    assert candidates[0].status == ResurfacingStatus.SELECTED


def test_record_resurfacing_updates_lifecycle_state(db_session):
    lifecycle_repo = FirestoreLifecycleRepository(db_session)
    resurfacing_repo = FirestoreResurfacingRepository(db_session)
    service = ResurfacingService(lifecycle_repo, resurfacing_repo)

    lifecycle_repo.upsert_assignment(_past_due_assignment("item-due"))
    candidates = service.get_revisit_candidates("user-1")

    presented = service.record_resurfacing(candidates[0].resurfacing_id, "user-1")
    assert presented.status == ResurfacingStatus.PRESENTED

    assignment = lifecycle_repo.get_by_item_id("item-due", "user-1")
    assert assignment.current_state == LifecycleState.RESURFACED
