from typing import List
from fastapi import APIRouter, Depends, HTTPException
from backend.domain.schemas.users import User
from backend.security.authentication import get_current_user
from backend.repositories.interfaces.event_repository import EventRepository
from backend.repositories.interfaces.item_repository import ItemRepository
from backend.repositories.factory import get_event_repository, get_item_repository
from backend.services.event_service import EventService
from backend.services.item_service import ItemService

router = APIRouter(prefix="/history", tags=["History"])

def get_event_service(repo: EventRepository = Depends(get_event_repository)) -> EventService:
    return EventService(repo)

def get_item_service(repo: ItemRepository = Depends(get_item_repository)) -> ItemService:
    return ItemService(repo)

@router.get("/{item_id}")
def get_item_history(
    item_id: str,
    limit: int = 50,
    user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
    item_service: ItemService = Depends(get_item_service),
):
    item = item_service.get_item(item_id, user.user_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    events = event_service.list_for_item(user.user_id, item_id, limit=limit)
    return {
        "item_id": item_id,
        "events": [
            {"event_type": e.event_type, "occurred_at": e.occurred_at.isoformat(), "status": e.status.value}
            for e in events
        ],
    }
