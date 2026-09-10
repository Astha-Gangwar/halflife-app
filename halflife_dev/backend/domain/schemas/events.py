from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from backend.utils.clock import utcnow
from backend.domain.enums import ActorType, EventStatus

class Event(BaseModel):
    event_id: str
    user_id: str
    item_id: Optional[str] = None
    analysis_id: Optional[str] = None
    resurfacing_id: Optional[str] = None
    event_type: str
    actor_type: ActorType
    actor_id: Optional[str] = None
    source: str
    status: EventStatus = EventStatus.SUCCEEDED
    occurred_at: datetime = Field(default_factory=utcnow)
    correlation_id: str
    causation_event_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
