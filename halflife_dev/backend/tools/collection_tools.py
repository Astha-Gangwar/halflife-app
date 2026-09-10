from typing import Optional, Dict, Any
from google.adk.tools.tool_context import ToolContext

from backend.tools.db_session import tool_db_session
from backend.tools.envelope import success_envelope, as_tool_envelope
from backend.repositories.firestore.firestore_collection_repository import FirestoreCollectionRepository
from backend.services.collection_service import CollectionService


@as_tool_envelope("manage_collection")
def manage_collection(
    tool_context: ToolContext,
    action: str,
    collection_id: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    item_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create, rename, archive, or manage item membership in a collection.

    action: 'create', 'rename', 'archive', 'add_item', or 'remove_item'.
    """
    user_id = tool_context.user_id
    with tool_db_session() as db:
        service = CollectionService(FirestoreCollectionRepository(db))

        if action == "create":
            if not name:
                raise ValueError("INVALID_PAYLOAD: name is required to create a collection")
            collection = service.create_collection(user_id, name, description)
            return success_envelope("manage_collection", {"collection_id": collection.collection_id, "name": collection.name})

        if action == "rename":
            if not collection_id or not name:
                raise ValueError("INVALID_PAYLOAD: collection_id and name are required to rename a collection")
            collection = service.rename_collection(user_id, collection_id, name)
            return success_envelope("manage_collection", {"collection_id": collection.collection_id, "name": collection.name})

        if action == "archive":
            if not collection_id:
                raise ValueError("INVALID_PAYLOAD: collection_id is required to archive a collection")
            collection = service.archive_collection(user_id, collection_id)
            return success_envelope("manage_collection", {"collection_id": collection.collection_id, "status": collection.status})

        if action == "add_item":
            if not collection_id or not item_id:
                raise ValueError("INVALID_PAYLOAD: collection_id and item_id are required")
            membership = service.add_item(user_id, collection_id, item_id)
            return success_envelope("manage_collection", {"membership_id": membership.membership_id})

        if action == "remove_item":
            if not collection_id or not item_id:
                raise ValueError("INVALID_PAYLOAD: collection_id and item_id are required")
            service.remove_item(user_id, collection_id, item_id)
            return success_envelope("manage_collection", {"collection_id": collection_id, "item_id": item_id, "removed": True})

        raise ValueError(f"INVALID_ACTION: '{action}' is not a supported collection action")
