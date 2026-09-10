from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List, Optional
from backend.domain.schemas.items import SavedItem, SavedItemCreate, ItemPatch
from backend.domain.schemas.users import User
from backend.security.authentication import get_current_user, require_mutation_allowed
from backend.repositories.interfaces.item_repository import ItemRepository
from backend.repositories.interfaces.idempotency_repository import IdempotencyRepository
from backend.repositories.factory import get_item_repository, get_idempotency_repository
from backend.services.item_service import ItemService
from backend.services.idempotency import apply_idempotency, IdempotencyConflict

router = APIRouter(prefix="/items", tags=["Items"])

def get_item_service(repo: ItemRepository = Depends(get_item_repository)) -> ItemService:
    return ItemService(repo)

def get_idempotency_repo(repo: IdempotencyRepository = Depends(get_idempotency_repository)) -> IdempotencyRepository:
    return repo

@router.post("/", response_model=SavedItem)
def create_item(
    item_create: SavedItemCreate,
    user: User = Depends(require_mutation_allowed),
    service: ItemService = Depends(get_item_service),
    idempotency_repo: IdempotencyRepository = Depends(get_idempotency_repo),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    if item_create.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to create for this user")

    try:
        existing = apply_idempotency(idempotency_repo, user.user_id, idempotency_key, "create_item", item_create.model_dump(mode="json"))
    except IdempotencyConflict as e:
        raise HTTPException(status_code=409, detail=str(e))

    if existing is not None:
        return existing.response_snapshot

    created = service.create_item(item_create)
    if idempotency_key:
        idempotency_repo.complete(user.user_id, idempotency_key, "create_item", created.item_id, created.model_dump(mode="json"))
    return created

@router.get("/", response_model=List[SavedItem])
def search_items(
    query: str = "",
    limit: int = 50,
    user: User = Depends(get_current_user),
    service: ItemService = Depends(get_item_service)
):
    return service.search_items(user.user_id, query, limit)

@router.get("/{item_id}", response_model=SavedItem)
def get_item(
    item_id: str,
    user: User = Depends(get_current_user),
    service: ItemService = Depends(get_item_service)
):
    item = service.get_item(item_id, user.user_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.patch("/{item_id}", response_model=SavedItem)
def update_item(
    item_id: str,
    patch: ItemPatch,
    user: User = Depends(require_mutation_allowed),
    service: ItemService = Depends(get_item_service)
):
    try:
        return service.update_item(item_id, user.user_id, patch)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/{item_id}/status", response_model=SavedItem)
def change_item_status(
    item_id: str,
    action: str,
    user: User = Depends(require_mutation_allowed),
    service: ItemService = Depends(get_item_service)
):
    """Batch 5 §6.5 change_item_status: archive, restore, or delete."""
    try:
        return service.change_item_status(item_id, user.user_id, action)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
