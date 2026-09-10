from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.domain.schemas.relationships import Relationship, RelationshipCandidate
from backend.domain.schemas.users import User
from backend.security.authentication import get_current_user, require_mutation_allowed
from backend.domain.enums import RelationshipType
from backend.repositories.interfaces.relationship_repository import RelationshipRepository
from backend.repositories.factory import get_relationship_repository
from backend.services.relationship_service import RelationshipService

router = APIRouter(prefix="/relationships", tags=["Relationships"])

def get_relationship_service(repo: RelationshipRepository = Depends(get_relationship_repository)) -> RelationshipService:
    return RelationshipService(repo)

class ConfirmRelationshipRequest(BaseModel):
    candidate_id: str
    source_item_id: str
    target_item_id: str
    relationship_type: RelationshipType
    reason: str

@router.get("/item/{item_id}/candidates", response_model=List[RelationshipCandidate])
def list_candidates(
    item_id: str,
    user: User = Depends(get_current_user),
    service: RelationshipService = Depends(get_relationship_service),
):
    return service.list_candidates_for_item(user.user_id, item_id)

@router.get("/item/{item_id}", response_model=List[Relationship])
def list_relationships(
    item_id: str,
    user: User = Depends(get_current_user),
    service: RelationshipService = Depends(get_relationship_service),
):
    return service.list_for_item(user.user_id, item_id)

@router.post("/confirm", response_model=Relationship)
def confirm_relationship(
    request: ConfirmRelationshipRequest,
    user: User = Depends(require_mutation_allowed),
    service: RelationshipService = Depends(get_relationship_service),
):
    try:
        return service.confirm_relationship(
            user.user_id, request.candidate_id, request.source_item_id,
            request.target_item_id, request.relationship_type, request.reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/candidates/{candidate_id}/reject", response_model=RelationshipCandidate)
def reject_candidate(
    candidate_id: str,
    user: User = Depends(require_mutation_allowed),
    service: RelationshipService = Depends(get_relationship_service),
):
    return service.reject_candidate(user.user_id, candidate_id)

@router.post("/{relationship_id}/remove", response_model=Relationship)
def remove_relationship(
    relationship_id: str,
    user: User = Depends(require_mutation_allowed),
    service: RelationshipService = Depends(get_relationship_service),
):
    try:
        return service.remove_relationship(user.user_id, relationship_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
