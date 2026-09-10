from fastapi import APIRouter, Depends, HTTPException
from typing import List
from backend.domain.schemas.users import User
from backend.security.authentication import get_current_user, require_mutation_allowed
from backend.domain.schemas.lifecycle import ResurfacingCandidate
from backend.domain.enums import OutcomeType
from backend.services.resurfacing_service import ResurfacingService
from backend.services.lifecycle_service import LifecycleService
from backend.services.item_service import ItemService
from backend.repositories.interfaces.lifecycle_repository import LifecycleRepository
from backend.repositories.interfaces.resurfacing_repository import ResurfacingRepository
from backend.repositories.interfaces.item_repository import ItemRepository
from backend.repositories.factory import (
    get_lifecycle_repository, get_resurfacing_repository, get_item_repository,
)

router = APIRouter(prefix="/revisit", tags=["Revisit"])

def get_resurfacing_service(
    lifecycle_repo: LifecycleRepository = Depends(get_lifecycle_repository),
    resurfacing_repo: ResurfacingRepository = Depends(get_resurfacing_repository),
) -> ResurfacingService:
    return ResurfacingService(lifecycle_repo, resurfacing_repo)

def get_lifecycle_service(repo: LifecycleRepository = Depends(get_lifecycle_repository)) -> LifecycleService:
    return LifecycleService(repo)

def get_item_service(repo: ItemRepository = Depends(get_item_repository)) -> ItemService:
    return ItemService(repo)

@router.get("/candidates", response_model=List[ResurfacingCandidate])
def get_revisit_candidates(
    limit: int = 10,
    user: User = Depends(get_current_user),
    service: ResurfacingService = Depends(get_resurfacing_service)
):
    """
    PF-06: Revisit an Item
    Returns items eligible for revisit based on lifecycle policy.
    """
    return service.get_revisit_candidates(user.user_id, limit=limit)

@router.post("/outcome")
def record_outcome(
    item_id: str,
    outcome: str,
    user: User = Depends(require_mutation_allowed),
    lifecycle_service: LifecycleService = Depends(get_lifecycle_service),
    item_service: ItemService = Depends(get_item_service),
):
    """
    PF-07: Record Outcome and Feedback
    """
    item = item_service.get_item(item_id, user.user_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    try:
        outcome_enum = OutcomeType(outcome)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid outcome: {outcome}")

    try:
        assignment = lifecycle_service.update_item_outcome(
            item_id, user.user_id, item.intent_type, outcome_enum,
            intent_attributes=item.intent_attributes,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return {
        "status": "success",
        "item_id": item_id,
        "lifecycle_state": assignment.current_state.value,
    }
