from abc import ABC, abstractmethod
from typing import List, Optional
from backend.domain.schemas.lifecycle import LifecycleAssignment

class LifecycleRepository(ABC):
    @abstractmethod
    def upsert_assignment(self, assignment: LifecycleAssignment) -> LifecycleAssignment:
        pass

    @abstractmethod
    def get_by_item_id(self, item_id: str, user_id: str) -> Optional[LifecycleAssignment]:
        pass
    
    @abstractmethod
    def get_revisit_candidates(self, user_id: str, limit: int = 10) -> List[LifecycleAssignment]:
        pass
