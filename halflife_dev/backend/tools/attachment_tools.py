from typing import Optional, Dict, Any
from google.adk.tools.tool_context import ToolContext

from backend.tools.db_session import tool_db_session
from backend.tools.envelope import success_envelope, as_tool_envelope
from backend.repositories.firestore.firestore_attachment_repository import FirestoreAttachmentRepository
from backend.services.attachment_service import AttachmentService


@as_tool_envelope("process_attachment")
def process_attachment(
    tool_context: ToolContext,
    item_id: str,
    storage_uri: str,
    original_filename: str,
    media_type: str,
    size_bytes: int,
    checksum: str,
) -> Dict[str, Any]:
    """Register and validate an attachment already uploaded to internal object
    storage by the client. This tool validates metadata (type, size) and
    marks the attachment available; it does not perform the upload itself —
    no object-storage client is wired up yet (Batch 9 storage layer, Phase 4+)."""
    user_id = tool_context.user_id
    with tool_db_session() as db:
        service = AttachmentService(FirestoreAttachmentRepository(db))
        attachment = service.register_attachment(
            user_id, item_id, storage_uri, original_filename, media_type, size_bytes, checksum,
        )
        attachment = service.mark_available(user_id, attachment.attachment_id)

    return success_envelope("process_attachment", {
        "attachment_id": attachment.attachment_id,
        "status": attachment.status,
    })
