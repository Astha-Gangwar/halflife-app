from abc import ABC, abstractmethod
from typing import Optional
from backend.domain.schemas.idempotency import IdempotencyRecord

class IdempotencyRepository(ABC):
    @abstractmethod
    def get(self, user_id: str, idempotency_key: str, operation: str) -> Optional[IdempotencyRecord]:
        pass

    @abstractmethod
    def create(self, record: IdempotencyRecord) -> IdempotencyRecord:
        pass

    @abstractmethod
    def complete(self, user_id: str, idempotency_key: str, operation: str, resource_id: Optional[str], response_snapshot: Optional[dict]) -> IdempotencyRecord:
        pass
