import uuid
from typing import List, Optional
from backend.domain.schemas.attachments import Attachment
from backend.repositories.interfaces.attachment_repository import AttachmentRepository

MAX_ATTACHMENT_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
SUPPORTED_MEDIA_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf", "text/plain"}

class AttachmentService:
    def __init__(self, attachment_repo: AttachmentRepository):
        self.attachment_repo = attachment_repo

    def register_attachment(self, user_id: str, item_id: str, storage_uri: str, original_filename: str, media_type: str, size_bytes: int, checksum: str) -> Attachment:
        if media_type not in SUPPORTED_MEDIA_TYPES:
            raise ValueError(f"UNSUPPORTED_MEDIA_TYPE: {media_type}")
        if size_bytes > MAX_ATTACHMENT_SIZE_BYTES:
            raise ValueError("FILE_TOO_LARGE")

        attachment = Attachment(
            attachment_id=str(uuid.uuid4()),
            user_id=user_id,
            item_id=item_id,
            storage_uri=storage_uri,
            original_filename=original_filename,
            media_type=media_type,
            size_bytes=size_bytes,
            checksum=checksum,
            status="uploading",
        )
        return self.attachment_repo.create(attachment)

    def mark_available(self, user_id: str, attachment_id: str, extracted_text: Optional[str] = None) -> Attachment:
        return self.attachment_repo.update_status(attachment_id, user_id, "available", extracted_text=extracted_text)

    def mark_rejected(self, user_id: str, attachment_id: str) -> Attachment:
        return self.attachment_repo.update_status(attachment_id, user_id, "rejected")

    def list_for_item(self, user_id: str, item_id: str) -> List[Attachment]:
        return self.attachment_repo.list_by_item(item_id, user_id)
