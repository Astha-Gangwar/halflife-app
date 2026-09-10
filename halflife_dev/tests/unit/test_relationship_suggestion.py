from types import SimpleNamespace
from unittest.mock import patch
from contextlib import contextmanager

from backend.tools import item_tools
from backend.repositories.firestore.firestore_relationship_repository import FirestoreRelationshipRepository


class _FakeToolContext(SimpleNamespace):
    pass


def _fake_context(user_id="user-1"):
    return _FakeToolContext(user_id=user_id)


@contextmanager
def _session_from(db_session):
    yield db_session


def test_creating_an_item_suggests_candidates_sharing_a_tag(db_session):
    """Regression test: RelationshipService.suggest_candidate() was fully
    implemented but never called from anywhere in the app -- no tool, no
    route, nothing -- so "Related memories" on the item detail page always
    showed empty, for every item, for every user. create_item should now
    suggest candidates against existing items that share an actual tag --
    category/type alone are surfaced only as supplementary context once a
    tag match justifies the suggestion (see the test below for why category/
    type alone must NOT be sufficient)."""
    with patch("backend.tools.item_tools.tool_db_session", lambda: _session_from(db_session)):
        first = item_tools.create_item(
            _fake_context(),
            original_content="Sourdough starter feeding schedule",
            intent="recipe",
            title="Sourdough starter",
            category="cooking",
            tags=["sourdough"],
        )
        first_id = first["result"]["item_id"]

        second = item_tools.create_item(
            _fake_context(),
            original_content="Sourdough bread baking notes",
            intent="recipe",
            title="Sourdough bread",
            category="cooking",
            tags=["sourdough"],
        )
        second_id = second["result"]["item_id"]

        repo = FirestoreRelationshipRepository(db_session)
        candidates = repo.list_candidates_for_item(second_id, "user-1")

    assert len(candidates) == 1
    assert candidates[0].source_item_id == second_id
    assert candidates[0].target_item_id == first_id
    assert "Shared tags: sourdough" in candidates[0].supporting_facts
    assert "Same category: cooking" in candidates[0].supporting_facts


def test_same_category_and_type_alone_does_not_suggest_a_relationship(db_session):
    """Regression test for the opposite failure: two unrelated tasks filed
    under the same broad category (e.g. two different "admin" errands) used
    to score high enough to be suggested as "related" just from category +
    intent_type matching, with zero actual topical connection. That's noise,
    not a relationship -- a shared tag is required now."""
    with patch("backend.tools.item_tools.tool_db_session", lambda: _session_from(db_session)):
        first = item_tools.create_item(
            _fake_context(),
            original_content="Renew passport before the trip",
            intent="task",
            title="Passport renewal",
            category="admin",
        )
        first_id = first["result"]["item_id"]

        second = item_tools.create_item(
            _fake_context(),
            original_content="Submit the quarterly project report",
            intent="task",
            title="Submit project",
            category="admin",
        )
        second_id = second["result"]["item_id"]

        repo = FirestoreRelationshipRepository(db_session)
        candidates = repo.list_candidates_for_item(second_id, "user-1")

    assert candidates == []
    assert first_id  # keep the first item referenced for clarity of intent


def test_creating_an_item_with_no_related_items_suggests_nothing(db_session):
    with patch("backend.tools.item_tools.tool_db_session", lambda: _session_from(db_session)):
        created = item_tools.create_item(
            _fake_context(),
            original_content="A completely unrelated one-off note",
            intent="general_note",
        )
        item_id = created["result"]["item_id"]

        repo = FirestoreRelationshipRepository(db_session)
        candidates = repo.list_candidates_for_item(item_id, "user-1")

    assert candidates == []
