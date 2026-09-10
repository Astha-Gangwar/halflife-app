from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from backend.utils.clock import utcnow
from backend.domain.enums import RelationshipType

class RelationshipCandidate(BaseModel):
    candidate_id: str
    user_id: str
    source_item_id: str
    target_item_id: str
    similarity_score: Optional[float] = None
    suggested_type: RelationshipType
    supporting_facts: List[str] = Field(default_factory=list)
    status: str = "suggested"  # suggested, accepted, rejected, expired
    created_at: datetime = Field(default_factory=utcnow)
    resolved_at: Optional[datetime] = None

class Relationship(BaseModel):
    relationship_id: str
    user_id: str
    source_item_id: str
    target_item_id: str
    relationship_type: RelationshipType
    reason: str
    created_by: str  # user, agent_suggestion_accepted, rule
    status: str = "confirmed"  # confirmed, removed
    created_at: datetime = Field(default_factory=utcnow)
    removed_at: Optional[datetime] = None
    version: int = 1
