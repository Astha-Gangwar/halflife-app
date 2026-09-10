from typing import List, Optional
from backend.domain.schemas.items import SavedItem, SavedItemCreate, ItemPatch
from backend.domain.enums import LifecycleState
from backend.repositories.interfaces.item_repository import ItemRepository

_VALID_STATUS_ACTIONS = {"archive", "restore", "delete"}

class ItemService:
    def __init__(self, item_repo: ItemRepository):
        self.item_repo = item_repo

    def create_item(self, item_create: SavedItemCreate) -> SavedItem:
        # Business rules around item creation can be enforced here.
        # e.g., default fields, limit checks
        return self.item_repo.create(item_create)

    def get_item(self, item_id: str, user_id: str) -> Optional[SavedItem]:
        return self.item_repo.get_by_id(item_id, user_id)

    def search_items(self, user_id: str, query: str, limit: int = 50) -> List[SavedItem]:
        return self.item_repo.search(user_id, query, limit)

    def update_item(self, item_id: str, user_id: str, patch: ItemPatch) -> SavedItem:
        return self.item_repo.update(item_id, user_id, patch)

    def archive_item(self, item_id: str, user_id: str) -> SavedItem:
        return self.item_repo.archive(item_id, user_id)

    def change_item_status(self, item_id: str, user_id: str, action: str) -> SavedItem:
        """Batch 5 §6.5 change_item_status: archive, restore, or delete."""
        if action not in _VALID_STATUS_ACTIONS:
            raise ValueError(f"INVALID_ACTION: {action}")
        if action == "archive":
            return self.item_repo.archive(item_id, user_id)
        if action == "restore":
            return self.item_repo.restore(item_id, user_id)
        return self.item_repo.delete(item_id, user_id)

    def sync_lifecycle_state(self, item_id: str, user_id: str, state: LifecycleState) -> SavedItem:
        return self.item_repo.sync_lifecycle_state(item_id, user_id, state)
