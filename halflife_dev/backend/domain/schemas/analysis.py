from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from backend.utils.clock import utcnow
from backend.domain.enums import IntentType, ConfidenceLevel, AnalysisStatus, ConfirmationStatus

class ValidationError(BaseModel):
    code: str
    field_path: Optional[str] = None
    message: str
    severity: str = "error"  # error, warning
    unsupported_value: Optional[Any] = None

class AnalysisResult(BaseModel):
    intent_type: Optional[IntentType] = None
    intent_confidence: float = 0.0
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    requires_confirmation: bool = False
    uncertainty_reason: Optional[str] = None
    suggested_title: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    intent_attributes: Optional[Dict[str, Any]] = None
    clarification_question: Optional[str] = None
    clarification_options: Optional[List[str]] = None
    possible_intents: List[IntentType] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    grounding_notes: List[str] = Field(default_factory=list)

class Analysis(BaseModel):
    analysis_id: str
    user_id: str
    item_draft_id: Optional[str] = None
    original_content_snapshot: str
    model_name: str
    model_version: str
    prompt_version: str
    model_result: Optional[AnalysisResult] = None
    validation_status: str = "pending"  # pending, passed, failed
    validation_errors: List[ValidationError] = Field(default_factory=list)
    status: AnalysisStatus = AnalysisStatus.REQUESTED
    confirmation_status: ConfirmationStatus = ConfirmationStatus.NOT_REQUIRED
    approved_result: Optional[AnalysisResult] = None
    item_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None

# Backwards-compatible alias for the earlier name used elsewhere in the codebase.
AnalysisRecord = Analysis

class ConfirmationResponse(BaseModel):
    analysis_id: str
    decision: str  # accept, correct, keep_general, edit_original, cancel
    selected_intent: Optional[IntentType] = None
    corrected_fields: Optional[Dict[str, Any]] = None
    user_comment: Optional[str] = None
    submitted_at: datetime = Field(default_factory=utcnow)
    submitted_by: str
