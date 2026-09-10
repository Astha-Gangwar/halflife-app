from typing import Optional, List, Dict, Any
from google.adk.tools.tool_context import ToolContext

from backend.tools.db_session import tool_db_session
from backend.tools.envelope import success_envelope, as_tool_envelope
from backend.repositories.firestore.firestore_preference_repository import FirestorePreferenceRepository
from backend.services.preference_service import PreferenceService


@as_tool_envelope("get_user_preferences")
def get_user_preferences(tool_context: ToolContext) -> Dict[str, Any]:
    """Retrieve the user's explicit lifecycle/resurfacing preferences."""
    user_id = tool_context.user_id
    with tool_db_session() as db:
        preferences = PreferenceService(FirestorePreferenceRepository(db)).get_preferences(user_id)

    return success_envelope("get_user_preferences", preferences.model_dump(mode="json"))


@as_tool_envelope("update_user_preferences")
def update_user_preferences(
    tool_context: ToolContext,
    timezone: Optional[str] = None,
    preferred_recipe_days: Optional[List[str]] = None,
    preferred_review_period: Optional[str] = None,
    max_recipe_effort_minutes: Optional[int] = None,
    max_learning_effort_minutes: Optional[int] = None,
    revisit_frequency_limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Update the user's explicit preferences. Only supplied fields change."""
    user_id = tool_context.user_id
    with tool_db_session() as db:
        preferences = PreferenceService(FirestorePreferenceRepository(db)).update_preferences(
            user_id,
            timezone=timezone,
            preferred_recipe_days=preferred_recipe_days,
            preferred_review_period=preferred_review_period,
            max_recipe_effort_minutes=max_recipe_effort_minutes,
            max_learning_effort_minutes=max_learning_effort_minutes,
            revisit_frequency_limit=revisit_frequency_limit,
        )

    return success_envelope("update_user_preferences", preferences.model_dump(mode="json"), resource_version=preferences.version)
