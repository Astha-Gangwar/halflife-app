from abc import ABC, abstractmethod
from typing import List
from backend.domain.schemas.feedback import Feedback

class FeedbackRepository(ABC):
    @abstractmethod
    def create(self, feedback: Feedback) -> Feedback:
        pass

    @abstractmethod
    def list_by_item(self, item_id: str, user_id: str) -> List[Feedback]:
        pass
