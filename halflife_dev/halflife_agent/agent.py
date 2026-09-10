from google.adk.agents.llm_agent import Agent

from halflife_agent.instructions import build_root_agent_instruction
from backend.tools.item_tools import create_item, get_item, search_items, update_item, change_item_status, find_similar_items
from backend.tools.lifecycle_tools import assign_lifecycle, get_revisit_candidates, record_resurfacing
from backend.tools.outcome_tools import update_item_outcome, record_feedback
from backend.tools.relationship_tools import manage_relationship
from backend.tools.collection_tools import manage_collection
from backend.tools.preference_tools import get_user_preferences, update_user_preferences
from backend.tools.attachment_tools import process_attachment
from backend.tools.link_tools import retrieve_link_content
from backend.tools.history_tools import get_item_history, compare_activity_history

# Configurable: pin to whichever Gemini model this deployment is provisioned
# for. gemini-2.0-flash was retired by the API (returns 404 as of Sept 2026).
# gemini-3.6-flash shows up in Vertex AI's models.list() for this project but
# 404s on generateContent -- likely not actually rolled out for this
# project/region despite being listed. gemini-2.5-flash is a stable,
# non-preview model confirmed available here; confirm against your actual
# Vertex AI / AI Studio access before deploying elsewhere.
AGENT_MODEL = "gemini-2.5-flash"

root_agent = Agent(
    model=AGENT_MODEL,
    name="halflife_memory_agent",
    description="Semantic orchestrator for the HalfLife personal memory application.",
    instruction=build_root_agent_instruction,
    tools=[
        create_item,
        get_item,
        search_items,
        update_item,
        change_item_status,
        find_similar_items,
        assign_lifecycle,
        get_revisit_candidates,
        record_resurfacing,
        update_item_outcome,
        record_feedback,
        manage_relationship,
        manage_collection,
        get_user_preferences,
        update_user_preferences,
        process_attachment,
        retrieve_link_content,
        get_item_history,
        compare_activity_history,
    ],
)
