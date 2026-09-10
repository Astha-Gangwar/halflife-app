import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from backend.domain.schemas.users import User
from backend.domain.schemas.items import SavedItemCreate
from backend.domain.schemas.analysis import AnalysisResult
from backend.domain.enums import IntentType, ConfidenceLevel
from backend.security.authentication import get_current_user, require_mutation_allowed
from backend.security.sensitive_content import looks_like_credential
from backend.repositories.interfaces.item_repository import ItemRepository
from backend.repositories.interfaces.analysis_repository import AnalysisRepository
from backend.repositories.factory import get_item_repository, get_analysis_repository
from backend.services.item_service import ItemService
from backend.services.analysis_service import AnalysisService
from backend.agent_runner import run_agent_turn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/capture", tags=["Capture"])

class CaptureRequest(BaseModel):
    content: str
    idempotency_key: str

def _agent_call_failed(e: Exception) -> HTTPException:
    """Turn any failure from run_agent_turn into a clean, user-safe error.

    The raw exception (e.g. Google's own _ResourceExhaustedError) can
    contain the entire provider error payload — doc links, quota metrics,
    JSON blobs — which must never reach the end user verbatim. The real
    detail is logged server-side for debugging; the client only ever sees
    a short, actionable sentence.
    """
    error_text = str(e)
    if "RESOURCE_EXHAUSTED" in error_text or "429" in error_text:
        logger.warning("Agent call rate-limited or over quota: %s", error_text)
        return HTTPException(
            status_code=429,
            detail="The AI assistant has hit its usage limit for now. Please try again in a minute.",
        )
    logger.error("Agent call failed: %s", error_text)
    return HTTPException(
        status_code=503,
        detail="The AI assistant is temporarily unavailable. Please try again shortly.",
    )

def get_item_service(repo: ItemRepository = Depends(get_item_repository)) -> ItemService:
    return ItemService(repo)

def get_analysis_service(repo: AnalysisRepository = Depends(get_analysis_repository)) -> AnalysisService:
    return AnalysisService(repo)

def _save_without_agent_analysis(user: User, content: str, item_service: ItemService, analysis_service: AnalysisService) -> dict:
    """Content that looks like it contains a password/credential is saved
    directly, without ever being sent to the external Gemini API — the
    tradeoff is no automatic intent classification for this one item."""
    analysis = analysis_service.record_analysis(
        user_id=user.user_id,
        original_content=content,
        model_result=AnalysisResult(
            intent_type=IntentType.GENERAL_NOTE,
            confidence=ConfidenceLevel.LOW,
            requires_confirmation=False,
            suggested_title="Saved note (withheld from AI analysis)",
            grounding_notes=[
                "Content appears to contain a password or credential; withheld "
                "from external model analysis and saved as-is."
            ],
        ),
        model_name="none", model_version="n/a", prompt_version="n/a",
    )
    item = item_service.create_item(SavedItemCreate(
        user_id=user.user_id,
        original_content=content,
        approved_title=analysis.model_result.suggested_title,
        intent_type=IntentType.GENERAL_NOTE,
        approved_analysis_id=analysis.analysis_id,
    ))
    return {
        "status": "success",
        "message": (
            "This looked like it might contain a password or credential, so it "
            "was saved as a plain note without being sent to the AI for analysis."
        ),
        "item_created": True,
        "item_id": item.item_id,
        "is_refusal": False,
    }

@router.post("/")
async def capture_item(
    request: CaptureRequest,
    user: User = Depends(require_mutation_allowed),
    item_service: ItemService = Depends(get_item_service),
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    """
    PF-01: Capture an item.
    Invokes the ADK agent, which classifies intent and — when confident
    enough and not requiring confirmation — calls create_item itself via
    its registered tools. The agent's own text response (which may be a
    clarification question, or a confirmation of what was saved) is
    returned as-is; it is not re-interpreted here.

    Exception: content that looks like it contains a password or other
    credential is never sent to the agent at all — it's saved directly
    (see _save_without_agent_analysis).
    """
    if looks_like_credential(request.content):
        return _save_without_agent_analysis(user, request.content, item_service, analysis_service)

    try:
        agent_result = await run_agent_turn(user.user_id, request.content)
    except Exception as e:
        raise _agent_call_failed(e)

    return {
        "status": "success",
        "message": agent_result.message,
        "item_created": agent_result.item_created,
        "item_id": agent_result.item_id,
        "is_refusal": agent_result.is_refusal,
    }

class ConfirmCaptureRequest(BaseModel):
    original_content: str
    corrections: Optional[Dict[str, Any]] = None
    analysis_id: Optional[str] = None

@router.post("/confirm")
async def confirm_capture(
    request: ConfirmCaptureRequest,
    user: User = Depends(require_mutation_allowed)
):
    """
    PF-02: Resolve Ambiguous Content / Confirm Understanding.

    Every call to run_agent_turn starts a brand-new, memory-less ADK
    session (see agent_runner.py) — the agent cannot recall a prior turn's
    content on its own. A confirm/correction request must therefore resend
    the original content itself, not just a reference to it. `analysis_id`
    is accepted but currently decorative: there is no persisted Analysis
    record on this path to look it up against (unlike the credential-
    detection path in _save_without_agent_analysis, which does create a
    real one) — it's included here so a future version can wire that up
    without changing this request shape again.
    """
    correction_text = f'Here is the content to save: "{request.original_content}".'
    if request.corrections:
        correction_text += f" Apply these corrections: {request.corrections}."
    else:
        correction_text += " Please save it as understood, with no further changes."

    try:
        agent_result = await run_agent_turn(user.user_id, correction_text)
    except Exception as e:
        raise _agent_call_failed(e)

    return {
        "status": "success",
        "message": agent_result.message,
        "item_created": agent_result.item_created,
        "item_id": agent_result.item_id,
        "is_refusal": agent_result.is_refusal,
    }
