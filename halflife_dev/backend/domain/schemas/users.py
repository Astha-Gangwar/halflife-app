from pydantic import BaseModel, Field
from datetime import datetime
from backend.utils.clock import utcnow
from typing import Optional

class User(BaseModel):
    user_id: str
    auth_subject: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    status: str = "active"  # active, disabled, deleted
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    deleted_at: Optional[datetime] = None
    version: int = 1
    last_login_at: Optional[datetime] = None
