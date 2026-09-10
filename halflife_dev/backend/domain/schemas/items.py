from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from backend.utils.clock import utcnow
from backend.domain.enums import ItemStatus, LifecycleState, IntentType, ContentFormat

class SavedItemBase(BaseModel):
    user_id: str
    original_content: str
    content_format: ContentFormat = ContentFormat.TEXT
    user_title: Optional[str] = None
    user_note: Optional[str] = None
    approved_title: str
    approved_summary: Optional[str] = None
    intent_type: IntentType
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    intent_attributes: Dict[str, Any] = Field(default_factory=dict)
    approved_analysis_id: str

class SavedItemCreate(SavedItemBase):
    pass

class SavedItem(SavedItemBase):
    item_id: str
    status: ItemStatus = ItemStatus.ACTIVE
    current_lifecycle_state: LifecycleState = LifecycleState.SAVED
    version: int = 1
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    archived_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

class ItemPatch(BaseModel):
    user_title: Optional[str] = None
    user_note: Optional[str] = None
    approved_title: Optional[str] = None
    approved_summary: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    intent_attributes: Optional[Dict[str, Any]] = None
    expected_version: int
