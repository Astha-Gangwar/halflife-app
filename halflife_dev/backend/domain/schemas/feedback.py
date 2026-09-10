from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from backend.utils.clock import utcnow

class Feedback(BaseModel):
    feedback_id: str
    user_id: str
    item_id: str
    resurfacing_id: Optional[str] = None
    feedback_type: str
    selected_value: str
    comment: Optional[str] = None
    submitted_at: datetime = Field(default_factory=utcnow)
    supersedes_feedback_id: Optional[str] = None
    version: int = 1
