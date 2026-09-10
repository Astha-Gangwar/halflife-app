import uuid
from typing import List, Optional
from backend.domain.schemas.collections import Collection, CollectionMembership
from backend.repositories.interfaces.collection_repository import CollectionRepository

class CollectionService:
    def __init__(self, collection_repo: CollectionRepository):
        self.collection_repo = collection_repo

    def create_collection(self, user_id: str, name: str, description: Optional[str] = None, suggested_by_system: bool = False) -> Collection:
        collection = Collection(
            collection_id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            description=description,
            suggested_by_system=suggested_by_system,
        )
        return self.collection_repo.create(collection)

    def rename_collection(self, user_id: str, collection_id: str, name: str) -> Collection:
        return self.collection_repo.update(collection_id, user_id, name=name)

    def archive_collection(self, user_id: str, collection_id: str) -> Collection:
        return self.collection_repo.update(collection_id, user_id, status="archived")

    def add_item(self, user_id: str, collection_id: str, item_id: str, added_by: str = "user") -> CollectionMembership:
        membership = CollectionMembership(
            membership_id=str(uuid.uuid4()),
            user_id=user_id,
            collection_id=collection_id,
            item_id=item_id,
            added_by=added_by,
        )
        return self.collection_repo.add_membership(membership)

    def remove_item(self, user_id: str, collection_id: str, item_id: str) -> None:
        self.collection_repo.remove_membership(collection_id, item_id, user_id)

    def list_collections(self, user_id: str) -> List[Collection]:
        return self.collection_repo.list_by_user(user_id)

    def list_items(self, user_id: str, collection_id: str) -> List[str]:
        return self.collection_repo.list_items(collection_id, user_id)
