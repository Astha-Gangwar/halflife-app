from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from backend.utils.clock import utcnow

class IdempotencyRecord(BaseModel):
    user_id: str
    idempotency_key: str
    operation: str
    request_hash: str
    status: str = "in_progress"  # in_progress, completed, failed
    resource_id: Optional[str] = None
    response_snapshot: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=utcnow)
    expires_at: datetime
