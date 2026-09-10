from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from backend.utils.clock import utcnow

class Attachment(BaseModel):
    attachment_id: str
    user_id: str
    item_id: str
    storage_uri: str
    original_filename: str
    media_type: str
    size_bytes: int
    checksum: str
    status: str = "uploading"  # uploading, available, rejected, deleted
    extracted_text: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    deleted_at: Optional[datetime] = None
