from abc import ABC, abstractmethod
from typing import List, Optional
from backend.domain.schemas.attachments import Attachment

class AttachmentRepository(ABC):
    @abstractmethod
    def create(self, attachment: Attachment) -> Attachment:
        pass

    @abstractmethod
    def get_by_id(self, attachment_id: str, user_id: str) -> Optional[Attachment]:
        pass

    @abstractmethod
    def list_by_item(self, item_id: str, user_id: str) -> List[Attachment]:
        pass

    @abstractmethod
    def update_status(self, attachment_id: str, user_id: str, status: str, extracted_text: Optional[str] = None) -> Attachment:
        pass
