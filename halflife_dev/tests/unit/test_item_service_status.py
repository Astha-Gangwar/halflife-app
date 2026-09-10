import pytest
from backend.repositories.firestore.firestore_item_repository import FirestoreItemRepository
from backend.services.item_service import ItemService
from backend.domain.schemas.items import SavedItemCreate
from backend.domain.enums import IntentType, ItemStatus


def _make_item(service, user_id="user-1"):
    return service.create_item(SavedItemCreate(
        user_id=user_id,
        original_content="Some content",
        approved_title="Title",
        intent_type=IntentType.GENERAL_NOTE,
        approved_analysis_id="an-1",
    ))


def test_change_item_status_archive_restore_delete(db_session):
    service = ItemService(FirestoreItemRepository(db_session))
    item = _make_item(service)

    archived = service.change_item_status(item.item_id, "user-1", "archive")
    assert archived.status == ItemStatus.ARCHIVED

    restored = service.change_item_status(item.item_id, "user-1", "restore")
    assert restored.status == ItemStatus.ACTIVE
    assert restored.archived_at is None

    deleted = service.change_item_status(item.item_id, "user-1", "delete")
    assert deleted.status == ItemStatus.DELETED
    assert deleted.deleted_at is not None


def test_change_item_status_rejects_invalid_action(db_session):
    service = ItemService(FirestoreItemRepository(db_session))
    item = _make_item(service)

    with pytest.raises(ValueError):
        service.change_item_status(item.item_id, "user-1", "not_a_real_action")
