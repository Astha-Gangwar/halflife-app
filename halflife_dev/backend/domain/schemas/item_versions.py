from pydantic import BaseModel, Field
from datetime import datetime
from backend.utils.clock import utcnow
from backend.domain.enums import ActorType
from backend.domain.schemas.items import SavedItem

class ItemVersion(BaseModel):
    item_version_id: str
    user_id: str
    item_id: str
    version_number: int
    snapshot: SavedItem
    change_type: str  # user_edit, reanalysis, correction, lifecycle_update
    changed_by: ActorType
    created_at: datetime = Field(default_factory=utcnow)
