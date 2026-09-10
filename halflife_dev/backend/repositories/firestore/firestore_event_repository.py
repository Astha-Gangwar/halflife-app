from typing import List
from collections import Counter
from backend.repositories.interfaces.event_repository import EventRepository
from backend.domain.schemas.events import Event
from backend.domain.enums import ActorType, EventStatus
from backend.utils.clock import normalize_firestore_datetimes

COLLECTION = "events"


class FirestoreEventRepository(EventRepository):
    def __init__(self, db):
        self.db = db

    def create(self, event: Event) -> Event:
        doc = {
            "event_id": event.event_id,
            "user_id": event.user_id,
            "item_id": event.item_id,
            "analysis_id": event.analysis_id,
            "resurfacing_id": event.resurfacing_id,
            "event_type": event.event_type,
            "actor_type": event.actor_type.value,
            "actor_id": event.actor_id,
            "source": event.source,
            "status": event.status.value,
            "occurred_at": event.occurred_at,
            "correlation_id": event.correlation_id,
            "causation_event_id": event.causation_event_id,
            "event_metadata": dict(event.metadata),
        }
        self.db.collection(COLLECTION).document(event.event_id).set(doc)
        return self._to_domain(doc)

    def list_by_item(self, item_id: str, user_id: str, limit: int = 100) -> List[Event]:
        query = (
            self.db.collection(COLLECTION)
            .where("item_id", "==", item_id)
            .where("user_id", "==", user_id)
            .order_by("occurred_at", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        return [self._to_domain(s.to_dict()) for s in query]

    def count_by_type(self, user_id: str) -> dict:
        query = self.db.collection(COLLECTION).where("user_id", "==", user_id).stream()
        counts = Counter(s.to_dict().get("event_type") for s in query)
        return dict(counts)

    def _to_domain(self, data: dict) -> Event:
        data = normalize_firestore_datetimes(data)
        return Event(
            event_id=data["event_id"],
            user_id=data["user_id"],
            item_id=data.get("item_id"),
            analysis_id=data.get("analysis_id"),
            resurfacing_id=data.get("resurfacing_id"),
            event_type=data["event_type"],
            actor_type=ActorType(data["actor_type"]),
            actor_id=data.get("actor_id"),
            source=data["source"],
            status=EventStatus(data["status"]),
            occurred_at=data["occurred_at"],
            correlation_id=data["correlation_id"],
            causation_event_id=data.get("causation_event_id"),
            metadata=data.get("event_metadata") or {},
        )
