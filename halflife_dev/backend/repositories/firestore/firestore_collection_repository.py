from typing import List, Optional
from datetime import datetime
from backend.utils.clock import utcnow, normalize_firestore_datetimes
from backend.repositories.interfaces.collection_repository import CollectionRepository
from backend.domain.schemas.collections import Collection, CollectionMembership

COLLECTIONS_COLLECTION = "collections"
MEMBERSHIPS_COLLECTION = "collection_memberships"


class FirestoreCollectionRepository(CollectionRepository):
    def __init__(self, db):
        self.db = db

    def create(self, collection: Collection) -> Collection:
        doc = {
            "collection_id": collection.collection_id,
            "user_id": collection.user_id,
            "name": collection.name,
            "description": collection.description,
            "suggested_by_system": collection.suggested_by_system,
            "status": collection.status,
            "created_at": collection.created_at,
            "updated_at": collection.updated_at,
            "version": collection.version,
        }
        self.db.collection(COLLECTIONS_COLLECTION).document(collection.collection_id).set(doc)
        return self._to_domain(doc)

    def get_by_id(self, collection_id: str, user_id: str) -> Optional[Collection]:
        snap = self.db.collection(COLLECTIONS_COLLECTION).document(collection_id).get()
        if not snap.exists:
            return None
        data = snap.to_dict()
        if data.get("user_id") != user_id:
            return None
        return self._to_domain(data)

    def list_by_user(self, user_id: str) -> List[Collection]:
        query = self.db.collection(COLLECTIONS_COLLECTION).where("user_id", "==", user_id).stream()
        return [self._to_domain(s.to_dict()) for s in query]

    def update(self, collection_id: str, user_id: str, name: Optional[str] = None, description: Optional[str] = None, status: Optional[str] = None) -> Collection:
        doc_ref = self.db.collection(COLLECTIONS_COLLECTION).document(collection_id)
        snap = doc_ref.get()
        if not snap.exists or snap.to_dict().get("user_id") != user_id:
            raise ValueError("COLLECTION_NOT_FOUND_OR_NOT_ACCESSIBLE: collection not found or unauthorized")
        data = snap.to_dict()
        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if status is not None:
            updates["status"] = status
        updates["updated_at"] = utcnow()
        updates["version"] = data.get("version", 1) + 1
        doc_ref.update(updates)
        data.update(updates)
        return self._to_domain(data)

    def add_membership(self, membership: CollectionMembership) -> CollectionMembership:
        doc = {
            "membership_id": membership.membership_id,
            "user_id": membership.user_id,
            "collection_id": membership.collection_id,
            "item_id": membership.item_id,
            "added_by": membership.added_by,
            "created_at": membership.created_at,
            "removed_at": membership.removed_at,
        }
        self.db.collection(MEMBERSHIPS_COLLECTION).document(membership.membership_id).set(doc)
        return CollectionMembership(**doc)

    def remove_membership(self, collection_id: str, item_id: str, user_id: str) -> None:
        query = self.db.collection(MEMBERSHIPS_COLLECTION).where(
            "collection_id", "==", collection_id
        ).where("item_id", "==", item_id).where("user_id", "==", user_id).limit(1).stream()
        snap = next(iter(query), None)
        if snap is not None:
            snap.reference.update({"removed_at": utcnow()})

    def list_items(self, collection_id: str, user_id: str) -> List[str]:
        query = self.db.collection(MEMBERSHIPS_COLLECTION).where(
            "collection_id", "==", collection_id
        ).where("user_id", "==", user_id).stream()
        item_ids = []
        for snap in query:
            data = snap.to_dict()
            if data.get("removed_at") is None:
                item_ids.append(data["item_id"])
        return item_ids

    def _to_domain(self, data: dict) -> Collection:
        data = normalize_firestore_datetimes(data)
        return Collection(
            collection_id=data["collection_id"],
            user_id=data["user_id"],
            name=data["name"],
            description=data.get("description"),
            suggested_by_system=bool(data.get("suggested_by_system", False)),
            status=data["status"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            version=data["version"],
        )
