from unittest.mock import MagicMock

from backend.utils.clock import utcnow
from halflife_agent.instructions import build_root_agent_instruction


def test_instruction_includes_todays_real_date():
    """Regression test for the "buy milk tomorrow" bug: the agent must be
    told the real current date on every turn (not a date frozen at process
    startup), or it has no honest basis for resolving a relative date
    phrase into a real calendar date."""
    instruction = build_root_agent_instruction(MagicMock())
    today_str = utcnow().strftime("%Y-%m-%d")
    assert today_str in instruction


def test_instruction_names_the_exact_due_at_field_and_forbids_raw_phrases():
    instruction = build_root_agent_instruction(MagicMock())
    assert '"due_at"' in instruction
    assert "never the original relative phrase" in instruction


def test_instruction_forbids_exposing_internal_ids_to_the_user():
    """Regression test: a live UI test showed the agent including the raw
    item_id UUID in its user-facing confirmation message — meaningless
    internal noise for a person reading the response."""
    instruction = build_root_agent_instruction(MagicMock())
    assert "item_id" in instruction
    assert "Never mention an item_id" in instruction


def test_instruction_gives_a_general_category_list_for_normal_items():
    """Regression test: normal items (not reference material) had no
    category guidance at all, so the agent always left `category` unset
    and every item showed as "Uncategorized" in the UI. The general list
    must be present, and distinct from the six reference-material strings
    it sits alongside."""
    instruction = build_root_agent_instruction(MagicMock())
    for category in [
        "cooking", "fitness", "health", "home", "admin",
        "work", "learning", "product-ideas", "personal", "notes",
    ]:
        assert f'"{category}"' in instruction
