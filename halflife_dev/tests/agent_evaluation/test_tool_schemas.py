"""Agent tool-contract tests (Batch 5 §22 "Agent selection tests").

True agent-selection evaluation — does the LLM actually pick the right tool
for a given user utterance — requires a live Gemini API key and is out of
scope here (see backend/agent_runner.py; there's no GOOGLE_API_KEY in this
environment). What *can* be verified deterministically, and is the
foundation any real evaluation harness would sit on top of, is that every
tool the agent can call has a well-formed schema: `tool_context` is never
exposed to the model, and every genuinely required business argument is
marked required.
"""
from google.adk.tools.function_tool import FunctionTool

from halflife_agent.agent import root_agent


def _declaration_for(tool_name: str):
    for tool in root_agent.tools:
        if getattr(tool, "__name__", None) == tool_name:
            return FunctionTool(tool)._get_declaration()
    raise AssertionError(f"No registered tool named {tool_name!r}")


def test_all_nineteen_tools_are_registered():
    names = {getattr(t, "__name__", None) for t in root_agent.tools}
    expected = {
        "create_item", "get_item", "search_items", "update_item", "change_item_status",
        "find_similar_items", "assign_lifecycle", "get_revisit_candidates", "record_resurfacing",
        "update_item_outcome", "record_feedback", "manage_relationship", "manage_collection",
        "get_user_preferences", "update_user_preferences", "process_attachment",
        "retrieve_link_content", "get_item_history", "compare_activity_history",
    }
    assert expected.issubset(names)


def test_tool_context_is_never_exposed_to_the_model():
    """AUTH-007: tool arguments supplied by the model cannot override trusted
    ownership context — tool_context (which carries user_id) must never
    appear in a tool's schema."""
    for tool in root_agent.tools:
        decl = FunctionTool(tool)._get_declaration()
        properties = (decl.parameters_json_schema or {}).get("properties", {})
        assert "tool_context" not in properties, f"{tool.__name__} leaks tool_context to the model"


def test_create_item_requires_the_fields_it_cannot_function_without():
    decl = _declaration_for("create_item")
    required = set(decl.parameters_json_schema["required"])
    assert {"original_content", "intent"} <= required
    # approved_analysis_id is a server-generated internal correlation id, not
    # something the model has any real value to supply -- it must never be a
    # model-suppliable argument (an omitted value used to silently fail the
    # whole capture).
    assert "approved_analysis_id" not in decl.parameters_json_schema["properties"]
    # user_id must never be a model-suppliable argument (comes from tool_context).
    assert "user_id" not in decl.parameters_json_schema["properties"]


def test_update_item_requires_expected_version_for_optimistic_concurrency():
    decl = _declaration_for("update_item")
    required = set(decl.parameters_json_schema["required"])
    assert "expected_version" in required
    assert "item_id" in required


def test_every_tool_has_a_non_empty_description():
    """The agent relies on the description to decide when to call a tool at
    all (Batch 5 §15) — an empty description is a silent tool-selection bug."""
    for tool in root_agent.tools:
        decl = FunctionTool(tool)._get_declaration()
        assert decl.description and len(decl.description.strip()) > 10, f"{tool.__name__} has no usable description"
