from typing import List
from backend.repositories.interfaces.feedback_repository import FeedbackRepository
from backend.domain.schemas.feedback import Feedback
from backend.utils.clock import normalize_firestore_datetimes

COLLECTION = "feedback"


class FirestoreFeedbackRepository(FeedbackRepository):
    def __init__(self, db):
        self.db = db

    def create(self, feedback: Feedback) -> Feedback:
        doc = feedback.model_dump()
        self.db.collection(COLLECTION).document(feedback.feedback_id).set(doc)
        return self._to_domain(doc)

    def list_by_item(self, item_id: str, user_id: str) -> List[Feedback]:
        query = self.db.collection(COLLECTION).where("item_id", "==", item_id).where(
            "user_id", "==", user_id
        ).stream()
        return [self._to_domain(s.to_dict()) for s in query]

    def _to_domain(self, data: dict) -> Feedback:
        data = normalize_firestore_datetimes(data)
        return Feedback(
            feedback_id=data["feedback_id"],
            user_id=data["user_id"],
            item_id=data["item_id"],
            resurfacing_id=data.get("resurfacing_id"),
            feedback_type=data["feedback_type"],
            selected_value=data["selected_value"],
            comment=data.get("comment"),
            submitted_at=data["submitted_at"],
            supersedes_feedback_id=data.get("supersedes_feedback_id"),
            version=data["version"],
        )
