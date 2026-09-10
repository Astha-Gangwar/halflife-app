"""Interface-contract tests for LifecycleRepository, run against
FirestoreLifecycleRepository backed by an in-memory fake Firestore client
(see test_item_repository_contract.py for the full rationale)."""
import pytest
from datetime import timedelta
from backend.utils.clock import utcnow
from backend.repositories.firestore.firestore_lifecycle_repository import FirestoreLifecycleRepository
from backend.domain.schemas.lifecycle import LifecycleAssignment
from backend.domain.enums import LifecycleState


@pytest.fixture()
def lifecycle_repo(db_session):
    return FirestoreLifecycleRepository(db_session)


def _assignment(item_id="item-1", user_id="user-1", state=LifecycleState.SCHEDULED_FOR_REVIEW):
    import uuid
    return LifecycleAssignment(
        assignment_id=str(uuid.uuid4()),
        user_id=user_id,
        item_id=item_id,
        policy_version="v1.0",
        current_state=state,
        next_review_date=utcnow() - timedelta(days=1),
    )


def test_upsert_creates_then_updates_same_item(lifecycle_repo):
    created = lifecycle_repo.upsert_assignment(_assignment())
    assert created.version == 1

    updated = lifecycle_repo.upsert_assignment(_assignment(state=LifecycleState.DISMISSED))
    assert updated.version == 2
    assert updated.current_state == LifecycleState.DISMISSED


def test_get_by_item_id_enforces_ownership(lifecycle_repo):
    lifecycle_repo.upsert_assignment(_assignment(user_id="user-1"))
    assert lifecycle_repo.get_by_item_id("item-1", "user-1") is not None
    assert lifecycle_repo.get_by_item_id("item-1", "user-2") is None


def test_revisit_candidates_only_returns_scheduled_state(lifecycle_repo):
    lifecycle_repo.upsert_assignment(_assignment(item_id="scheduled", state=LifecycleState.SCHEDULED_FOR_REVIEW))
    lifecycle_repo.upsert_assignment(_assignment(item_id="completed", state=LifecycleState.COMPLETED))

    candidates = lifecycle_repo.get_revisit_candidates("user-1")
    item_ids = {c.item_id for c in candidates}
    assert item_ids == {"scheduled"}
