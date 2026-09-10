import uuid
from typing import Optional, List, Dict, Any
from google.adk.tools.tool_context import ToolContext

from backend.tools.db_session import tool_db_session
from backend.tools.envelope import success_envelope, as_tool_envelope
from backend.repositories.firestore.firestore_item_repository import FirestoreItemRepository
from backend.repositories.firestore.firestore_lifecycle_repository import FirestoreLifecycleRepository
from backend.repositories.firestore.firestore_relationship_repository import FirestoreRelationshipRepository
from backend.services.item_service import ItemService
from backend.services.lifecycle_service import LifecycleService
from backend.services.relationship_service import RelationshipService
from backend.domain.schemas.items import SavedItemCreate, ItemPatch, SavedItem
from backend.domain.enums import IntentType, RelationshipType


def _suggest_related_candidates(
    relationship_service: RelationshipService, item_service: ItemService, user_id: str, new_item: SavedItem,
) -> None:
    """Best-effort MVP relatedness signal: a shared tag is required -- two
    items merely filed under the same broad category or content type (e.g.
    two unrelated "admin" tasks) are not a meaningful relationship, and
    suggesting them as such just floods "Related memories" with noise (see
    the bug this replaced: every task was "related" to every other task).
    Category/type matches are still surfaced as supporting context once a
    real tag match justifies the suggestion in the first place.
    No embeddings/vector search exist yet, so this is a stand-in, not the
    eventual similarity architecture."""
    existing = [i for i in item_service.search_items(user_id, "", limit=200) if i.item_id != new_item.item_id]

    scored = []
    for other in existing:
        shared_tags = set(new_item.tags) & set(other.tags)
        if not shared_tags:
            continue
        score = len(shared_tags)
        if new_item.category and other.category == new_item.category:
            score += 1
        if other.intent_type == new_item.intent_type:
            score += 1
        scored.append((score, other, shared_tags))

    scored.sort(key=lambda triple: triple[0], reverse=True)
    for score, other, shared_tags in scored[:3]:
        facts = [f"Shared tags: {', '.join(sorted(shared_tags))}"]
        if new_item.category and other.category == new_item.category:
            facts.append(f"Same category: {new_item.category}")
        if other.intent_type == new_item.intent_type:
            facts.append(f"Same type: {new_item.intent_type.value}")
        relationship_service.suggest_candidate(
            user_id, new_item.item_id, other.item_id, RelationshipType.SIMILAR,
            similarity_score=min(score / 4, 1.0), supporting_facts=facts,
        )


@as_tool_envelope("create_item")
def create_item(
    tool_context: ToolContext,
    original_content: str,
    intent: str,
    title: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    intent_attributes: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Persist original content and its approved understanding as a new item.

    Call this only after the user has confirmed the analysis (or it's clear
    enough not to need confirmation) — never to save unconfirmed content.

    `tags` are the specific-topic keywords that drive related-item detection
    (see _suggest_related_candidates below) -- unlike `category`, which is
    broad (e.g. "admin"), tags should name what this item is actually about
    (e.g. "chrome-extension", "passport-renewal") so two items only get
    linked when they're genuinely about the same thing, not just filed under
    the same broad category.
    """
    user_id = tool_context.user_id
    intent_enum = IntentType(intent)

    with tool_db_session() as db:
        item_service = ItemService(FirestoreItemRepository(db))
        lifecycle_service = LifecycleService(FirestoreLifecycleRepository(db))

        saved_item = item_service.create_item(SavedItemCreate(
            user_id=user_id,
            original_content=original_content,
            intent_type=intent_enum,
            approved_title=title or original_content[:80],
            category=category,
            tags=tags or [],
            intent_attributes=intent_attributes or {},
            # Purely an internal correlation id -- nothing looks it up against a
            # real Analysis record on this path (see backend/api/routes/capture.py's
            # confirm_capture docstring), so there's no reason to make the model
            # invent one. It used to be a required model-supplied argument, which
            # meant an occasional missed/omitted value from the LLM silently
            # failed the entire capture.
            approved_analysis_id=str(uuid.uuid4()),
        ))

        assignment = lifecycle_service.assign_lifecycle(
            item_id=saved_item.item_id,
            user_id=user_id,
            intent=intent_enum,
            preferences={},
            intent_attributes=intent_attributes or {},
            category=category,
        )
        item_service.sync_lifecycle_state(saved_item.item_id, user_id, assignment.current_state)

        relationship_service = RelationshipService(FirestoreRelationshipRepository(db))
        _suggest_related_candidates(relationship_service, item_service, user_id, saved_item)

    return success_envelope(
        "create_item",
        {
            "item_id": saved_item.item_id,
            "approved_title": saved_item.approved_title,
            "status": saved_item.status.value,
            "lifecycle_state": assignment.current_state.value,
            "next_review_date": assignment.next_review_date.isoformat() if assignment.next_review_date else None,
        },
        resource_version=saved_item.version,
    )


@as_tool_envelope("get_item")
def get_item(tool_context: ToolContext, item_id: str) -> Dict[str, Any]:
    """Retrieve one authorized item. Never answer 'what's stored' from model memory — always call this."""
    user_id = tool_context.user_id
    with tool_db_session() as db:
        item = ItemService(FirestoreItemRepository(db)).get_item(item_id, user_id)

    if item is None:
        raise ValueError("ITEM_NOT_FOUND_OR_NOT_ACCESSIBLE: no item with that id for this user")

    return success_envelope("get_item", item.model_dump(mode="json"), resource_version=item.version)


@as_tool_envelope("search_items")
def search_items(tool_context: ToolContext, query: str, limit: int = 50) -> Dict[str, Any]:
    """Retrieve user-owned items matching a search query."""
    user_id = tool_context.user_id
    with tool_db_session() as db:
        items = ItemService(FirestoreItemRepository(db)).search_items(user_id, query, limit)

    return success_envelope("search_items", {"items": [i.model_dump(mode="json") for i in items]})


@as_tool_envelope("update_item")
def update_item(
    tool_context: ToolContext,
    item_id: str,
    expected_version: int,
    approved_title: Optional[str] = None,
    approved_summary: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    intent_attributes: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Apply an explicit user correction to an item's approved fields."""
    user_id = tool_context.user_id
    patch = ItemPatch(
        approved_title=approved_title,
        approved_summary=approved_summary,
        category=category,
        tags=tags,
        intent_attributes=intent_attributes,
        expected_version=expected_version,
    )
    with tool_db_session() as db:
        updated = ItemService(FirestoreItemRepository(db)).update_item(item_id, user_id, patch)

    return success_envelope("update_item", updated.model_dump(mode="json"), resource_version=updated.version)


@as_tool_envelope("change_item_status")
def change_item_status(tool_context: ToolContext, item_id: str, action: str) -> Dict[str, Any]:
    """Archive, restore, or delete an item through an approved control."""
    user_id = tool_context.user_id
    with tool_db_session() as db:
        updated = ItemService(FirestoreItemRepository(db)).change_item_status(item_id, user_id, action)

    return success_envelope("change_item_status", {"item_id": item_id, "status": updated.status.value}, resource_version=updated.version)


@as_tool_envelope("find_similar_items")
def find_similar_items(tool_context: ToolContext, item_id: str, limit: int = 5) -> Dict[str, Any]:
    """Return user-owned candidates related to an item.

    MVP note: this uses a text-overlap search rather than real embedding
    similarity (no EmbeddingAdapter/vector index exists yet) — the ranking
    is a coarse stand-in, not the Batch 9 similarity architecture.
    """
    user_id = tool_context.user_id
    with tool_db_session() as db:
        item_service = ItemService(FirestoreItemRepository(db))
        source = item_service.get_item(item_id, user_id)
        if source is None:
            raise ValueError("ITEM_NOT_FOUND_OR_NOT_ACCESSIBLE: source item not found")
        candidates = item_service.search_items(user_id, source.original_content[:50], limit + 1)

    candidates = [c for c in candidates if c.item_id != item_id][:limit]
    return success_envelope("find_similar_items", {
        "candidates": [{"item_id": c.item_id, "title": c.approved_title, "content": c.original_content} for c in candidates]
    })
