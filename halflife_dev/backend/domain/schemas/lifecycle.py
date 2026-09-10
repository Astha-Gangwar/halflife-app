from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from backend.utils.clock import utcnow
from backend.domain.enums import LifecycleState, ResurfacingStatus

class LifecycleAssignment(BaseModel):
    assignment_id: str
    user_id: str
    item_id: str
    policy_id: str = "default"
    policy_version: str
    current_state: LifecycleState
    next_review_date: Optional[datetime] = None
    eligible_from: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None
    reason: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    version: int = 1

class ResurfacingCandidate(BaseModel):
    resurfacing_id: str
    user_id: str
    item_id: str
    assignment_id: str
    status: ResurfacingStatus = ResurfacingStatus.CANDIDATE
    eligibility_reason_code: str
    supporting_facts: Dict[str, Any] = Field(default_factory=dict)
    rank_score: Optional[float] = None
    rank_factors: Dict[str, Any] = Field(default_factory=dict)
    eligible_at: datetime
    selected_at: Optional[datetime] = None
    presented_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)
