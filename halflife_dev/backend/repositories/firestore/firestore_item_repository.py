import uuid
from typing import List, Optional
from datetime import datetime
from backend.utils.clock import utcnow, normalize_firestore_datetimes
from backend.repositories.interfaces.item_repository import ItemRepository
from backend.domain.schemas.items import SavedItem, SavedItemCreate, ItemPatch
from backend.domain.enums import ItemStatus, LifecycleState, IntentType, ContentFormat

COLLECTION = "items"


class FirestoreItemRepository(ItemRepository):
    def __init__(self, db):
        self.db = db

    def create(self, item_create: SavedItemCreate) -> SavedItem:
        now = utcnow()
        new_id = str(uuid.uuid4())

        doc = {
            "item_id": new_id,
            "user_id": item_create.user_id,
            "original_content": item_create.original_content,
            "content_format": item_create.content_format.value,
            "user_title": item_create.user_title,
            "user_note": item_create.user_note,
            "approved_title": item_create.approved_title,
            "approved_summary": item_create.approved_summary,
            "intent_type": item_create.intent_type.value,
            "category": item_create.category,
            "tags": list(item_create.tags),
            "intent_attributes": dict(item_create.intent_attributes),
            "approved_analysis_id": item_create.approved_analysis_id,
            "status": ItemStatus.ACTIVE.value,
            "current_lifecycle_state": LifecycleState.SAVED.value,
            "version": 1,
            "created_at": now,
            "updated_at": now,
            "archived_at": None,
            "deleted_at": None,
        }
        self.db.collection(COLLECTION).document(new_id).set(doc)
        return self._to_domain(doc)

    def get_by_id(self, item_id: str, user_id: str) -> Optional[SavedItem]:
        snap = self.db.collection(COLLECTION).document(item_id).get()
        if not snap.exists:
            return None
        data = snap.to_dict()
        if data.get("user_id") != user_id:
            return None
        return self._to_domain(data)

    def search(self, user_id: str, query: str, limit: int = 50) -> List[SavedItem]:
        # Firestore has no substring/LIKE query support, so this mirrors the
        # sqlite implementation's semantics (substring match on
        # original_content) by filtering client-side after scoping to the
        # user. Fine for MVP data volumes.
        query_lower = (query or "").lower()
        docs = self.db.collection(COLLECTION).where("user_id", "==", user_id).stream()
        results = []
        for snap in docs:
            data = snap.to_dict()
            # Archived/deleted items must not keep showing up in normal
            # browsing (Library, Home) just because their status field
            # changed -- there's no dedicated "Archived" view in the UI to
            # see them again, so leaving them in here made Archive and
            # Delete both no-ops from the user's point of view.
            if data.get("status") in (ItemStatus.ARCHIVED.value, ItemStatus.DELETED.value):
                continue
            if query_lower in (data.get("original_content") or "").lower():
                results.append(data)
            if len(results) >= limit:
                break
        return [self._to_domain(d) for d in results]

    def update(self, item_id: str, user_id: str, patch: ItemPatch) -> SavedItem:
        doc_ref = self.db.collection(COLLECTION).document(item_id)
        snap = doc_ref.get()
        if not snap.exists or snap.to_dict().get("user_id") != user_id:
            raise ValueError("ITEM_NOT_FOUND_OR_NOT_ACCESSIBLE: item not found or unauthorized")
        data = snap.to_dict()
        if data.get("version") != patch.expected_version:
            raise ValueError("VERSION_CONFLICT: version conflict")

        updates = {}
        if patch.user_title is not None:
            updates["user_title"] = patch.user_title
        if patch.user_note is not None:
            updates["user_note"] = patch.user_note
        if patch.approved_title is not None:
            updates["approved_title"] = patch.approved_title
        if patch.approved_summary is not None:
            updates["approved_summary"] = patch.approved_summary
        if patch.category is not None:
            updates["category"] = patch.category
        if patch.tags is not None:
            updates["tags"] = list(patch.tags)
        if patch.intent_attributes is not None:
            updates["intent_attributes"] = dict(patch.intent_attributes)

        updates["version"] = data.get("version", 1) + 1
        updates["updated_at"] = utcnow()

        doc_ref.update(updates)
        data.update(updates)
        return self._to_domain(data)

    def archive(self, item_id: str, user_id: str) -> SavedItem:
        return self._transition(item_id, user_id, {
            "status": ItemStatus.ARCHIVED.value,
            "archived_at": utcnow(),
        })

    def restore(self, item_id: str, user_id: str) -> SavedItem:
        return self._transition(item_id, user_id, {
            "status": ItemStatus.ACTIVE.value,
            "archived_at": None,
            "deleted_at": None,
        })

    def delete(self, item_id: str, user_id: str) -> SavedItem:
        return self._transition(item_id, user_id, {
            "status": ItemStatus.DELETED.value,
            "deleted_at": utcnow(),
        })

    def sync_lifecycle_state(self, item_id: str, user_id: str, state: LifecycleState) -> SavedItem:
        return self._transition(item_id, user_id, {
            "current_lifecycle_state": state.value,
        })

    def _transition(self, item_id: str, user_id: str, changes: dict) -> SavedItem:
        doc_ref = self.db.collection(COLLECTION).document(item_id)
        snap = doc_ref.get()
        if not snap.exists or snap.to_dict().get("user_id") != user_id:
            raise ValueError("ITEM_NOT_FOUND_OR_NOT_ACCESSIBLE: item not found or unauthorized")
        data = snap.to_dict()
        changes["updated_at"] = utcnow()
        changes["version"] = data.get("version", 1) + 1
        doc_ref.update(changes)
        data.update(changes)
        return self._to_domain(data)

    def _to_domain(self, data: dict) -> SavedItem:
        data = normalize_firestore_datetimes(data)
        return SavedItem(
            item_id=data["item_id"],
            user_id=data["user_id"],
            original_content=data["original_content"],
            content_format=ContentFormat(data["content_format"]),
            user_title=data.get("user_title"),
            user_note=data.get("user_note"),
            approved_title=data["approved_title"],
            approved_summary=data.get("approved_summary"),
            intent_type=IntentType(data["intent_type"]),
            category=data.get("category"),
            tags=data.get("tags") or [],
            intent_attributes=data.get("intent_attributes") or {},
            approved_analysis_id=data["approved_analysis_id"],
            status=ItemStatus(data["status"]),
            current_lifecycle_state=LifecycleState(data["current_lifecycle_state"]),
            version=data["version"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            archived_at=data.get("archived_at"),
            deleted_at=data.get("deleted_at"),
        )
