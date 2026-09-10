from abc import ABC, abstractmethod
from typing import List, Optional
from backend.domain.schemas.events import Event

class EventRepository(ABC):
    @abstractmethod
    def create(self, event: Event) -> Event:
        pass

    @abstractmethod
    def list_by_item(self, item_id: str, user_id: str, limit: int = 100) -> List[Event]:
        pass

    @abstractmethod
    def count_by_type(self, user_id: str) -> dict:
        pass
