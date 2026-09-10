"""Interface-contract tests for ItemRepository (Batch 5 §22 "Regression
tests"): the observable behavior every ItemRepository method must honor,
independent of any one service or route that happens to call it.

Runs against FirestoreItemRepository, backed by an in-memory fake Firestore
client (`mock-firestore`) rather than real GCP — fast, free, and offline,
while still exercising the actual repository code (collection/document
reads and writes), not a hand-rolled stand-in.
"""
from backend.repositories.firestore.firestore_item_repository import FirestoreItemRepository
from backend.domain.schemas.items import SavedItemCreate, ItemPatch
from backend.domain.enums import IntentType, ItemStatus
import pytest


@pytest.fixture()
def item_repo(db_session):
    return FirestoreItemRepository(db_session)


def _make_item_payload(user_id="user-1"):
    return SavedItemCreate(
        user_id=user_id,
        original_content="Learn about transformers",
        approved_title="Transformers 101",
        intent_type=IntentType.LEARNING_CONTENT,
        approved_analysis_id="an-1",
    )


def test_create_returns_active_item_with_version_one(item_repo):
    item = item_repo.create(_make_item_payload())
    assert item.status == ItemStatus.ACTIVE
    assert item.version == 1
    assert item.item_id  # a real id was assigned


def test_get_by_id_enforces_ownership(item_repo):
    item = item_repo.create(_make_item_payload(user_id="user-1"))
    assert item_repo.get_by_id(item.item_id, "user-1") is not None
    assert item_repo.get_by_id(item.item_id, "user-2") is None


def test_get_by_id_missing_returns_none(item_repo):
    assert item_repo.get_by_id("does-not-exist", "user-1") is None


def test_update_requires_matching_expected_version(item_repo):
    item = item_repo.create(_make_item_payload())
    updated = item_repo.update(item.item_id, item.user_id, ItemPatch(approved_title="New title", expected_version=1))
    assert updated.approved_title == "New title"
    assert updated.version == 2

    with pytest.raises(ValueError):
        item_repo.update(item.item_id, item.user_id, ItemPatch(approved_title="Stale", expected_version=1))


def test_update_wrong_owner_raises(item_repo):
    item = item_repo.create(_make_item_payload(user_id="user-1"))
    with pytest.raises(ValueError):
        item_repo.update(item.item_id, "user-2", ItemPatch(approved_title="Hijack", expected_version=1))


def test_archive_restore_delete_transitions(item_repo):
    item = item_repo.create(_make_item_payload())

    archived = item_repo.archive(item.item_id, item.user_id)
    assert archived.status == ItemStatus.ARCHIVED
    assert archived.archived_at is not None

    restored = item_repo.restore(item.item_id, item.user_id)
    assert restored.status == ItemStatus.ACTIVE
    assert restored.archived_at is None

    deleted = item_repo.delete(item.item_id, item.user_id)
    assert deleted.status == ItemStatus.DELETED
    assert deleted.deleted_at is not None


def test_search_scopes_to_owner_and_matches_content(item_repo):
    item_repo.create(_make_item_payload(user_id="user-1"))
    item_repo.create(_make_item_payload(user_id="user-2"))

    results = item_repo.search("user-1", "transformers")
    assert len(results) == 1
    assert results[0].user_id == "user-1"

    assert item_repo.search("user-1", "nonexistent-keyword") == []


def test_search_excludes_archived_and_deleted_items(item_repo):
    """Regression test: search() (which powers Library/Home) never
    filtered by status, so an archived or deleted item kept showing up
    everywhere -- Archive and Delete were both no-ops from the user's
    point of view."""
    active = item_repo.create(_make_item_payload(user_id="user-1"))
    archived = item_repo.create(_make_item_payload(user_id="user-1"))
    deleted = item_repo.create(_make_item_payload(user_id="user-1"))
    item_repo.archive(archived.item_id, "user-1")
    item_repo.delete(deleted.item_id, "user-1")

    results = item_repo.search("user-1", "")
    result_ids = {i.item_id for i in results}
    assert result_ids == {active.item_id}
