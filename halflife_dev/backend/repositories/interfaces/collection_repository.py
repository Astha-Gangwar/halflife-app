from abc import ABC, abstractmethod
from typing import List, Optional
from backend.domain.schemas.collections import Collection, CollectionMembership

class CollectionRepository(ABC):
    @abstractmethod
    def create(self, collection: Collection) -> Collection:
        pass

    @abstractmethod
    def get_by_id(self, collection_id: str, user_id: str) -> Optional[Collection]:
        pass

    @abstractmethod
    def list_by_user(self, user_id: str) -> List[Collection]:
        pass

    @abstractmethod
    def update(self, collection_id: str, user_id: str, name: Optional[str] = None, description: Optional[str] = None, status: Optional[str] = None) -> Collection:
        pass

    @abstractmethod
    def add_membership(self, membership: CollectionMembership) -> CollectionMembership:
        pass

    @abstractmethod
    def remove_membership(self, collection_id: str, item_id: str, user_id: str) -> None:
        pass

    @abstractmethod
    def list_items(self, collection_id: str, user_id: str) -> List[str]:
        pass
