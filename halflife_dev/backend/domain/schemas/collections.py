from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from backend.utils.clock import utcnow

class Collection(BaseModel):
    collection_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    suggested_by_system: bool = False
    status: str = "active"  # active, archived, deleted
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    version: int = 1

class CollectionMembership(BaseModel):
    membership_id: str
    user_id: str
    collection_id: str
    item_id: str
    added_by: str = "user"  # user, accepted_suggestion, rule
    created_at: datetime = Field(default_factory=utcnow)
    removed_at: Optional[datetime] = None
