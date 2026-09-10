from abc import ABC, abstractmethod
from typing import List, Optional
from backend.domain.schemas.lifecycle import ResurfacingCandidate

class ResurfacingRepository(ABC):
    @abstractmethod
    def create_candidate(self, candidate: ResurfacingCandidate) -> ResurfacingCandidate:
        pass

    @abstractmethod
    def get_by_id(self, resurfacing_id: str, user_id: str) -> Optional[ResurfacingCandidate]:
        pass

    @abstractmethod
    def update_status(self, resurfacing_id: str, user_id: str, status: str, presented_at=None) -> ResurfacingCandidate:
        pass

    @abstractmethod
    def list_by_status(self, user_id: str, status: str, limit: int = 50) -> List[ResurfacingCandidate]:
        pass
