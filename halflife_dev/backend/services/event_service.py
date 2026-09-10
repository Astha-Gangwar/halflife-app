import uuid
from typing import Optional, Dict, Any, List
from backend.domain.schemas.events import Event
from backend.domain.enums import ActorType, EventStatus
from backend.repositories.interfaces.event_repository import EventRepository

class EventService:
    """Thin, direct event-recording helper (Batch 5 §14 write_event capability).

    Not a generic event bus for MVP — state-changing services call this
    directly after a successful (or rejected/failed) mutation.
    """
    def __init__(self, event_repo: EventRepository):
        self.event_repo = event_repo

    def write_event(
        self,
        user_id: str,
        event_type: str,
        correlation_id: str,
        source: str,
        item_id: Optional[str] = None,
        analysis_id: Optional[str] = None,
        resurfacing_id: Optional[str] = None,
        actor_type: ActorType = ActorType.USER,
        actor_id: Optional[str] = None,
        status: EventStatus = EventStatus.SUCCEEDED,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Event:
        event = Event(
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            item_id=item_id,
            analysis_id=analysis_id,
            resurfacing_id=resurfacing_id,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            source=source,
            status=status,
            correlation_id=correlation_id,
            metadata=metadata or {},
        )
        return self.event_repo.create(event)

    def list_for_item(self, user_id: str, item_id: str, limit: int = 100) -> List[Event]:
        return self.event_repo.list_by_item(item_id, user_id, limit=limit)

    def count_by_type(self, user_id: str) -> Dict[str, int]:
        return self.event_repo.count_by_type(user_id)
