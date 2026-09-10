from typing import List, Optional
from backend.repositories.interfaces.attachment_repository import AttachmentRepository
from backend.domain.schemas.attachments import Attachment
from backend.utils.clock import normalize_firestore_datetimes

COLLECTION = "attachments"


class FirestoreAttachmentRepository(AttachmentRepository):
    def __init__(self, db):
        self.db = db

    def create(self, attachment: Attachment) -> Attachment:
        doc = attachment.model_dump()
        self.db.collection(COLLECTION).document(attachment.attachment_id).set(doc)
        return self._to_domain(doc)

    def get_by_id(self, attachment_id: str, user_id: str) -> Optional[Attachment]:
        snap = self.db.collection(COLLECTION).document(attachment_id).get()
        if not snap.exists:
            return None
        data = snap.to_dict()
        if data.get("user_id") != user_id:
            return None
        return self._to_domain(data)

    def list_by_item(self, item_id: str, user_id: str) -> List[Attachment]:
        query = self.db.collection(COLLECTION).where("item_id", "==", item_id).where(
            "user_id", "==", user_id
        ).stream()
        return [self._to_domain(s.to_dict()) for s in query]

    def update_status(self, attachment_id: str, user_id: str, status: str, extracted_text: Optional[str] = None) -> Attachment:
        doc_ref = self.db.collection(COLLECTION).document(attachment_id)
        snap = doc_ref.get()
        if not snap.exists or snap.to_dict().get("user_id") != user_id:
            raise ValueError("ATTACHMENT_NOT_FOUND_OR_NOT_ACCESSIBLE: attachment not found or unauthorized")
        data = snap.to_dict()
        updates = {"status": status}
        if extracted_text is not None:
            updates["extracted_text"] = extracted_text
        doc_ref.update(updates)
        data.update(updates)
        return self._to_domain(data)

    def _to_domain(self, data: dict) -> Attachment:
        data = normalize_firestore_datetimes(data)
        return Attachment(
            attachment_id=data["attachment_id"],
            user_id=data["user_id"],
            item_id=data["item_id"],
            storage_uri=data["storage_uri"],
            original_filename=data["original_filename"],
            media_type=data["media_type"],
            size_bytes=data["size_bytes"],
            checksum=data["checksum"],
            status=data["status"],
            extracted_text=data.get("extracted_text"),
            created_at=data["created_at"],
            deleted_at=data.get("deleted_at"),
        )
