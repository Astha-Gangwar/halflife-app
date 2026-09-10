"""Repository factory: one function per aggregate, each returning the
Firestore implementation of that aggregate's repository interface.

Route modules depend on these functions instead of constructing
`FirestoreXRepository(...)` directly, e.g.:

    from backend.repositories.factory import get_item_repository
    ...
    def get_item_service(repo: ItemRepository = Depends(get_item_repository)) -> ItemService:
        return ItemService(repo)

This project previously also supported a SQLite implementation, switched
via a `REPO_BACKEND` env var, for local development without GCP
credentials. That was removed in favor of Firestore exclusively — see
`tests/conftest.py` for how the test suite now provides Firestore access
(a fake in-memory client, not real GCP) instead of relying on SQLite.
"""
from backend.db.firestore_connection import get_firestore_client

from backend.repositories.interfaces.item_repository import ItemRepository
from backend.repositories.interfaces.lifecycle_repository import LifecycleRepository
from backend.repositories.interfaces.relationship_repository import RelationshipRepository
from backend.repositories.interfaces.collection_repository import CollectionRepository
from backend.repositories.interfaces.preference_repository import PreferenceRepository
from backend.repositories.interfaces.attachment_repository import AttachmentRepository
from backend.repositories.interfaces.feedback_repository import FeedbackRepository
from backend.repositories.interfaces.event_repository import EventRepository
from backend.repositories.interfaces.idempotency_repository import IdempotencyRepository
from backend.repositories.interfaces.analysis_repository import AnalysisRepository
from backend.repositories.interfaces.resurfacing_repository import ResurfacingRepository

from backend.repositories.firestore.firestore_item_repository import FirestoreItemRepository
from backend.repositories.firestore.firestore_lifecycle_repository import FirestoreLifecycleRepository
from backend.repositories.firestore.firestore_relationship_repository import FirestoreRelationshipRepository
from backend.repositories.firestore.firestore_collection_repository import FirestoreCollectionRepository
from backend.repositories.firestore.firestore_preference_repository import FirestorePreferenceRepository
from backend.repositories.firestore.firestore_attachment_repository import FirestoreAttachmentRepository
from backend.repositories.firestore.firestore_feedback_repository import FirestoreFeedbackRepository
from backend.repositories.firestore.firestore_event_repository import FirestoreEventRepository
from backend.repositories.firestore.firestore_idempotency_repository import FirestoreIdempotencyRepository
from backend.repositories.firestore.firestore_analysis_repository import FirestoreAnalysisRepository
from backend.repositories.firestore.firestore_resurfacing_repository import FirestoreResurfacingRepository


def get_item_repository() -> ItemRepository:
    return FirestoreItemRepository(get_firestore_client())


def get_lifecycle_repository() -> LifecycleRepository:
    return FirestoreLifecycleRepository(get_firestore_client())


def get_relationship_repository() -> RelationshipRepository:
    return FirestoreRelationshipRepository(get_firestore_client())


def get_collection_repository() -> CollectionRepository:
    return FirestoreCollectionRepository(get_firestore_client())


def get_preference_repository() -> PreferenceRepository:
    return FirestorePreferenceRepository(get_firestore_client())


def get_attachment_repository() -> AttachmentRepository:
    return FirestoreAttachmentRepository(get_firestore_client())


def get_feedback_repository() -> FeedbackRepository:
    return FirestoreFeedbackRepository(get_firestore_client())


def get_event_repository() -> EventRepository:
    return FirestoreEventRepository(get_firestore_client())


def get_idempotency_repository() -> IdempotencyRepository:
    return FirestoreIdempotencyRepository(get_firestore_client())


def get_analysis_repository() -> AnalysisRepository:
    return FirestoreAnalysisRepository(get_firestore_client())


def get_resurfacing_repository() -> ResurfacingRepository:
    return FirestoreResurfacingRepository(get_firestore_client())
