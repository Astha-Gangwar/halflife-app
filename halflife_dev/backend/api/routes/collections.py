from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.domain.schemas.collections import Collection, CollectionMembership
from backend.domain.schemas.users import User
from backend.security.authentication import get_current_user, require_mutation_allowed
from backend.repositories.interfaces.collection_repository import CollectionRepository
from backend.repositories.factory import get_collection_repository
from backend.services.collection_service import CollectionService

router = APIRouter(prefix="/collections", tags=["Collections"])

def get_collection_service(repo: CollectionRepository = Depends(get_collection_repository)) -> CollectionService:
    return CollectionService(repo)

class CreateCollectionRequest(BaseModel):
    name: str
    description: Optional[str] = None

class RenameCollectionRequest(BaseModel):
    name: str

@router.get("/", response_model=List[Collection])
def list_collections(
    user: User = Depends(get_current_user),
    service: CollectionService = Depends(get_collection_service),
):
    return service.list_collections(user.user_id)

@router.post("/", response_model=Collection)
def create_collection(
    request: CreateCollectionRequest,
    user: User = Depends(require_mutation_allowed),
    service: CollectionService = Depends(get_collection_service),
):
    return service.create_collection(user.user_id, request.name, request.description)

@router.patch("/{collection_id}", response_model=Collection)
def rename_collection(
    collection_id: str,
    request: RenameCollectionRequest,
    user: User = Depends(require_mutation_allowed),
    service: CollectionService = Depends(get_collection_service),
):
    try:
        return service.rename_collection(user.user_id, collection_id, request.name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{collection_id}/archive", response_model=Collection)
def archive_collection(
    collection_id: str,
    user: User = Depends(require_mutation_allowed),
    service: CollectionService = Depends(get_collection_service),
):
    try:
        return service.archive_collection(user.user_id, collection_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{collection_id}/items/{item_id}", response_model=CollectionMembership)
def add_item(
    collection_id: str,
    item_id: str,
    user: User = Depends(require_mutation_allowed),
    service: CollectionService = Depends(get_collection_service),
):
    return service.add_item(user.user_id, collection_id, item_id)

@router.delete("/{collection_id}/items/{item_id}")
def remove_item(
    collection_id: str,
    item_id: str,
    user: User = Depends(require_mutation_allowed),
    service: CollectionService = Depends(get_collection_service),
):
    service.remove_item(user.user_id, collection_id, item_id)
    return {"status": "success"}

@router.get("/{collection_id}/items", response_model=List[str])
def list_items(
    collection_id: str,
    user: User = Depends(get_current_user),
    service: CollectionService = Depends(get_collection_service),
):
    return service.list_items(user.user_id, collection_id)
