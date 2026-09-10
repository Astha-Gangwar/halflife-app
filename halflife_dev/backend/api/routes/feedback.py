from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.domain.schemas.feedback import Feedback
from backend.domain.schemas.users import User
from backend.security.authentication import get_current_user, require_mutation_allowed
from backend.repositories.interfaces.feedback_repository import FeedbackRepository
from backend.repositories.factory import get_feedback_repository
from backend.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["Feedback"])

def get_feedback_service(repo: FeedbackRepository = Depends(get_feedback_repository)) -> FeedbackService:
    return FeedbackService(repo)

class RecordFeedbackRequest(BaseModel):
    item_id: str
    feedback_type: str
    selected_value: str
    comment: Optional[str] = None
    resurfacing_id: Optional[str] = None

@router.post("/", response_model=Feedback)
def record_feedback(
    request: RecordFeedbackRequest,
    user: User = Depends(require_mutation_allowed),
    service: FeedbackService = Depends(get_feedback_service),
):
    return service.record_feedback(
        user.user_id, request.item_id, request.feedback_type, request.selected_value,
        comment=request.comment, resurfacing_id=request.resurfacing_id,
    )

@router.get("/item/{item_id}", response_model=List[Feedback])
def list_feedback(
    item_id: str,
    user: User = Depends(get_current_user),
    service: FeedbackService = Depends(get_feedback_service),
):
    return service.list_for_item(user.user_id, item_id)
