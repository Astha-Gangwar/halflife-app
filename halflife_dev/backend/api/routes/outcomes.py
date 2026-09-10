from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.domain.schemas.users import User
from backend.security.authentication import get_current_user, require_mutation_allowed
from backend.domain.enums import OutcomeType
from backend.repositories.interfaces.lifecycle_repository import LifecycleRepository
from backend.repositories.interfaces.item_repository import ItemRepository
from backend.repositories.factory import get_lifecycle_repository, get_item_repository
from backend.services.lifecycle_service import LifecycleService
from backend.services.item_service import ItemService

router = APIRouter(prefix="/outcomes", tags=["Outcomes"])

def get_lifecycle_service(repo: LifecycleRepository = Depends(get_lifecycle_repository)) -> LifecycleService:
    return LifecycleService(repo)

def get_item_service(repo: ItemRepository = Depends(get_item_repository)) -> ItemService:
    return ItemService(repo)

class RecordOutcomeRequest(BaseModel):
    outcome: str
    remind_at: Optional[str] = None

@router.post("/{item_id}")
def record_outcome(
    item_id: str,
    request: RecordOutcomeRequest,
    user: User = Depends(require_mutation_allowed),
    lifecycle_service: LifecycleService = Depends(get_lifecycle_service),
    item_service: ItemService = Depends(get_item_service),
):
    """Batch 5 §12.1 update_item_outcome: validate and apply a user-selected
    outcome (tried, completed, dismissed, modified, not_relevant, remind_later,
    archived, restored)."""
    item = item_service.get_item(item_id, user.user_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    try:
        outcome_enum = OutcomeType(request.outcome)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"INVALID_OUTCOME: '{request.outcome}'")

    remind_at_dt = datetime.fromisoformat(request.remind_at) if request.remind_at else None

    try:
        assignment = lifecycle_service.update_item_outcome(
            item_id, user.user_id, item.intent_type, outcome_enum,
            remind_at=remind_at_dt, intent_attributes=item.intent_attributes,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # The lifecycle_assignments record above is the source of truth, but the
    # item's own current_lifecycle_state is what every read path (the UI,
    # search filtering, Insights) actually displays/uses -- without this it
    # silently goes stale and the outcome looks like it was never recorded.
    item_service.sync_lifecycle_state(item_id, user.user_id, assignment.current_state)

    return {
        "item_id": item_id,
        "lifecycle_state": assignment.current_state.value,
        "next_review_date": assignment.next_review_date.isoformat() if assignment.next_review_date else None,
    }
