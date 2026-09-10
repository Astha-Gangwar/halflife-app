from typing import Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.domain.schemas.preferences import UserPreference
from backend.domain.schemas.users import User
from backend.security.authentication import get_current_user, require_mutation_allowed
from backend.repositories.interfaces.preference_repository import PreferenceRepository
from backend.repositories.factory import get_preference_repository
from backend.services.preference_service import PreferenceService

router = APIRouter(prefix="/preferences", tags=["Preferences"])

def get_preference_service(repo: PreferenceRepository = Depends(get_preference_repository)) -> PreferenceService:
    return PreferenceService(repo)

class UpdatePreferencesRequest(BaseModel):
    timezone: Optional[str] = None
    preferred_recipe_days: Optional[List[str]] = None
    preferred_review_period: Optional[str] = None
    max_recipe_effort_minutes: Optional[int] = None
    max_learning_effort_minutes: Optional[int] = None
    revisit_frequency_limit: Optional[int] = None

@router.get("/", response_model=UserPreference)
def get_preferences(
    user: User = Depends(get_current_user),
    service: PreferenceService = Depends(get_preference_service),
):
    return service.get_preferences(user.user_id)

@router.patch("/", response_model=UserPreference)
def update_preferences(
    request: UpdatePreferencesRequest,
    user: User = Depends(require_mutation_allowed),
    service: PreferenceService = Depends(get_preference_service),
):
    return service.update_preferences(user.user_id, **request.model_dump())
