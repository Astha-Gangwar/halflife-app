from abc import ABC, abstractmethod
from typing import List, Optional
from backend.domain.schemas.items import SavedItem, SavedItemCreate, ItemPatch
from backend.domain.enums import LifecycleState

class ItemRepository(ABC):
    @abstractmethod
    def create(self, item: SavedItemCreate) -> SavedItem:
        pass

    @abstractmethod
    def get_by_id(self, item_id: str, user_id: str) -> Optional[SavedItem]:
        pass
    
    @abstractmethod
    def search(self, user_id: str, query: str, limit: int = 50) -> List[SavedItem]:
        pass

    @abstractmethod
    def update(self, item_id: str, user_id: str, patch: ItemPatch) -> SavedItem:
        pass

    @abstractmethod
    def archive(self, item_id: str, user_id: str) -> SavedItem:
        pass

    @abstractmethod
    def restore(self, item_id: str, user_id: str) -> SavedItem:
        pass

    @abstractmethod
    def delete(self, item_id: str, user_id: str) -> SavedItem:
        pass

    @abstractmethod
    def sync_lifecycle_state(self, item_id: str, user_id: str, state: LifecycleState) -> SavedItem:
        """Mirror a lifecycle_assignments state change onto the item's own
        denormalized current_lifecycle_state field. Every caller that
        changes lifecycle state (assign_lifecycle, update_item_outcome)
        must call this too, or the item document silently goes stale --
        it's the field every read path (UI display, search filtering,
        Insights) actually uses, not the lifecycle_assignments record."""
        pass
