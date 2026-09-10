from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.domain.schemas.attachments import Attachment
from backend.domain.schemas.users import User
from backend.security.authentication import get_current_user, require_mutation_allowed
from backend.repositories.interfaces.attachment_repository import AttachmentRepository
from backend.repositories.factory import get_attachment_repository
from backend.services.attachment_service import AttachmentService

router = APIRouter(prefix="/attachments", tags=["Attachments"])

def get_attachment_service(repo: AttachmentRepository = Depends(get_attachment_repository)) -> AttachmentService:
    return AttachmentService(repo)

class RegisterAttachmentRequest(BaseModel):
    item_id: str
    storage_uri: str
    original_filename: str
    media_type: str
    size_bytes: int
    checksum: str

@router.post("/", response_model=Attachment)
def register_attachment(
    request: RegisterAttachmentRequest,
    user: User = Depends(require_mutation_allowed),
    service: AttachmentService = Depends(get_attachment_service),
):
    try:
        return service.register_attachment(
            user.user_id, request.item_id, request.storage_uri,
            request.original_filename, request.media_type, request.size_bytes, request.checksum,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/item/{item_id}", response_model=List[Attachment])
def list_attachments(
    item_id: str,
    user: User = Depends(get_current_user),
    service: AttachmentService = Depends(get_attachment_service),
):
    return service.list_for_item(user.user_id, item_id)
