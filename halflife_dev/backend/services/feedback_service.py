import uuid
from typing import List, Optional
from backend.domain.schemas.feedback import Feedback
from backend.repositories.interfaces.feedback_repository import FeedbackRepository

class FeedbackService:
    def __init__(self, feedback_repo: FeedbackRepository):
        self.feedback_repo = feedback_repo

    def record_feedback(self, user_id: str, item_id: str, feedback_type: str, selected_value: str, comment: Optional[str] = None, resurfacing_id: Optional[str] = None, supersedes_feedback_id: Optional[str] = None) -> Feedback:
        feedback = Feedback(
            feedback_id=str(uuid.uuid4()),
            user_id=user_id,
            item_id=item_id,
            resurfacing_id=resurfacing_id,
            feedback_type=feedback_type,
            selected_value=selected_value,
            comment=comment,
            supersedes_feedback_id=supersedes_feedback_id,
        )
        return self.feedback_repo.create(feedback)

    def list_for_item(self, user_id: str, item_id: str) -> List[Feedback]:
        return self.feedback_repo.list_by_item(item_id, user_id)
