from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.domain.schemas.analysis import Analysis
from backend.domain.schemas.users import User
from backend.security.authentication import get_current_user, require_mutation_allowed
from backend.repositories.interfaces.analysis_repository import AnalysisRepository
from backend.repositories.factory import get_analysis_repository
from backend.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analyses", tags=["Analyses"])

def get_analysis_service(repo: AnalysisRepository = Depends(get_analysis_repository)) -> AnalysisService:
    return AnalysisService(repo)

class ConfirmAnalysisRequest(BaseModel):
    decision: str  # accept, correct, keep_general, edit_original, cancel
    corrected_fields: Optional[Dict[str, Any]] = None
    user_comment: Optional[str] = None

@router.get("/{analysis_id}", response_model=Analysis)
def get_analysis(
    analysis_id: str,
    user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    analysis = service.get_analysis(analysis_id, user.user_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis

@router.post("/{analysis_id}/confirm", response_model=Analysis)
def confirm_analysis(
    analysis_id: str,
    confirmation: ConfirmAnalysisRequest,
    user: User = Depends(require_mutation_allowed),
    service: AnalysisService = Depends(get_analysis_service),
):
    # submitted_by is derived from the authenticated request context, not
    # accepted as a client-supplied field (Batch 5 AUTH-007).
    try:
        return service.confirm_analysis(analysis_id, user.user_id, confirmation.corrected_fields or {})
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
