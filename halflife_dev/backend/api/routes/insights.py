from fastapi import APIRouter, Depends
from backend.domain.schemas.users import User
from backend.security.authentication import get_current_user
from backend.repositories.interfaces.event_repository import EventRepository
from backend.repositories.interfaces.item_repository import ItemRepository
from backend.repositories.factory import get_event_repository, get_item_repository
from backend.services.event_service import EventService
from backend.services.insights_service import InsightsService

router = APIRouter(prefix="/insights", tags=["Insights"])

def get_event_service(repo: EventRepository = Depends(get_event_repository)) -> EventService:
    return EventService(repo)

def get_insights_service(repo: ItemRepository = Depends(get_item_repository)) -> InsightsService:
    return InsightsService(repo)

@router.get("/activity-summary")
def activity_summary(
    user: User = Depends(get_current_user),
    service: EventService = Depends(get_event_service),
):
    """Batch 5 Q-011: count factual events by type for basic insights.
    Deliberately just a count — no derived judgments or recommendations."""
    return {"event_counts_by_type": service.count_by_type(user.user_id)}

@router.get("/summary")
def summary(
    user: User = Depends(get_current_user),
    service: InsightsService = Depends(get_insights_service),
):
    """Insights page metrics, computed directly from the user's items —
    no separate analytics store needed since lifecycle state is already
    tracked per item."""
    return service.get_summary(user.user_id)
