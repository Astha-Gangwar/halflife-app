"""Seed (or refresh) the fixed, read-only demo account's data.

This is different from seed_synthetic_data.py in three ways:

1. Always targets the fixed DEMO_USER_ID ("demo" by default — see
   backend/security/authentication.py, which also enforces that this
   account can never be written to over the API).
2. Task due dates are computed relative to *today*, not hardcoded — some
   are already overdue, some due today, some due this week — so the
   Revisit page always has real, meaningful candidates no matter when a
   visitor actually opens the demo.
3. Idempotent: running it again wipes this account's previous items and
   lifecycle assignments first, then reseeds fresh. Re-run it periodically
   (daily is plenty) so the "due today" items stay honestly dated instead
   of drifting into the past forever.

Usage:
    python scripts/seed_demo_account.py

Requires GOOGLE_CLOUD_PROJECT set and Application Default Credentials
available, same as seed_synthetic_data.py.
"""
import os
import sys
from datetime import timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.domain.enums import IntentType, ContentFormat
from backend.domain.schemas.items import SavedItemCreate
from backend.services.item_service import ItemService
from backend.services.lifecycle_service import LifecycleService
from backend.utils.clock import utcnow
from backend.security.authentication import DEMO_USER_ID


def _analysis_id(tag: str) -> str:
    return f"demo-seed-{tag}"


def _reset_demo_account(firestore_client) -> None:
    """Delete every existing item, lifecycle assignment, collection, and
    collection membership for the demo account, so re-running this script
    never accumulates duplicates."""
    for collection_name in ("items", "lifecycle_assignments", "collections", "collection_memberships"):
        docs = firestore_client.collection(collection_name).where("user_id", "==", DEMO_USER_ID).stream()
        deleted = 0
        for doc in docs:
            firestore_client.collection(collection_name).document(doc.id).delete()
            deleted += 1
        print(f"  cleared {deleted} existing '{collection_name}' doc(s)")


def build_items(now):
    """Returns a list of (SavedItemCreate, group_key) pairs. group_key ties
    an item to one of the demo Collections built in main() — None means the
    item isn't grouped into any collection."""
    items = []

    def add(intent_type, title, content, summary, category, tags, attributes, group=None):
        items.append((SavedItemCreate(
            user_id=DEMO_USER_ID,
            original_content=content,
            content_format=ContentFormat.TEXT,
            approved_title=title,
            approved_summary=summary,
            intent_type=intent_type,
            category=category,
            tags=tags,
            intent_attributes=attributes,
            approved_analysis_id=_analysis_id(title.lower().replace(" ", "-")[:40]),
        ), group))

    iso = lambda dt: dt.strftime("%Y-%m-%d")

    # --- Tasks: dates computed relative to *today*, guaranteeing real
    # revisit candidates (overdue, due today, due this week) every time
    # this script runs, regardless of the actual calendar date. ---
    add(IntentType.TASK, "Renew passport",
        "Renew my passport, it expired last week",
        "Overdue passport renewal.", "admin", ["admin", "urgent"],
        {"action_text": "Renew passport", "priority": "high", "task_status": "open",
         "due_at": iso(now - timedelta(days=3))}, group="this_week")
    add(IntentType.TASK, "Pay electricity bill",
        "Pay the electricity bill, due yesterday",
        "Overdue utility bill.", "admin", ["bills"],
        {"action_text": "Pay electricity bill", "priority": "high", "task_status": "open",
         "due_at": iso(now - timedelta(days=1))}, group="this_week")
    add(IntentType.TASK, "Submit expense report",
        "Submit expense report for last month, due today",
        "Expense report due today.", "work", ["finance", "deadline"],
        {"action_text": "Submit expense report", "priority": "high", "task_status": "open",
         "due_at": iso(now)}, group="this_week")
    add(IntentType.TASK, "Call dentist",
        "Call the dentist to book a cleaning, due today",
        "Dentist booking due today.", "health", ["health"],
        {"action_text": "Call dentist", "priority": "medium", "task_status": "open",
         "due_at": iso(now)}, group="this_week")
    add(IntentType.TASK, "Book flight for conference",
        "Book flight for the conference next week",
        "Upcoming flight booking.", "work", ["travel"],
        {"action_text": "Book flight for conference", "priority": "medium", "task_status": "open",
         "due_at": iso(now + timedelta(days=4))}, group="this_week")
    add(IntentType.TASK, "Buy birthday gift",
        "Buy a birthday gift for mom, her birthday is this weekend",
        "Upcoming birthday gift.", "personal", ["gift", "family"],
        {"action_text": "Buy birthday gift for mom", "priority": "medium", "task_status": "open",
         "due_at": iso(now + timedelta(days=6))}, group="this_week")
    add(IntentType.TASK, "Renew car insurance",
        "Renew car insurance before it lapses next month",
        "Upcoming insurance renewal, no urgent date yet.", "admin", ["finance"],
        {"action_text": "Renew car insurance", "priority": "low", "task_status": "open"})
    add(IntentType.TASK, "Fix leaking kitchen faucet",
        "The kitchen faucet has been dripping for a while",
        "Home repair, not urgent.", "home", ["home-repair"],
        {"action_text": "Fix leaking kitchen faucet", "priority": "low", "task_status": "open"})

    # --- Activity logs: the "health tracker" narrative, spread over the
    # last two weeks with realistic, varied metrics. ---
    activity_log = [
        ("Morning 5K Run", "Ran 5km this morning, felt strong the whole way", "running", 5, 27, 3),
        ("Treadmill Interval Session", "20 minutes of treadmill intervals, alternating pace", "running", 3.2, 20, 5),
        ("Leg Day", "Leg day: squats 4x8 at 60kg, lunges, leg press", "strength_training", None, 55, 6),
        ("Upper Body Strength", "Bench press, rows, shoulder press — upper body day", "strength_training", None, 50, 8),
        ("Evening Swim", "Swam 20 laps at the pool", "swimming", 1.0, 40, 4),
        ("Cycling Commute", "Cycled to work instead of driving", "cycling", 15, None, 2),
        ("Yoga Recovery Session", "45 minute recovery-focused yoga class", "yoga", None, 45, 1),
        ("10K Long Run", "Longest run so far this training block — 10km", "running", 10, 58, 9),
        ("Rest Day Walk", "Easy 30 minute walk, active recovery", "walking", 2.5, 30, 10),
        ("Treadmill 5K Time Trial", "Timed 5km on the treadmill, new personal best", "running", 5, 24, 12),
    ]
    for title, content, activity_type, distance, duration, days_ago in activity_log:
        attrs = {"activity_type": activity_type, "completion_status": "completed"}
        if distance is not None:
            attrs["distance_km"] = distance
        if duration is not None:
            attrs["duration_minutes"] = duration
        add(IntentType.ACTIVITY_LOG, title, content, f"{activity_type.replace('_', ' ').title()} session.",
            "fitness", ["health-tracker", activity_type], attrs, group="fitness_log")

    # --- Recipes ---
    recipes = [
        ("Spaghetti Aglio e Olio", "Garlic, olive oil, chili flakes, parsley pasta", "pasta", 15, ["quick", "italian"]),
        ("Chicken Tikka Masala", "Marinated chicken in a creamy tomato curry sauce", "curry", 60, ["curry", "indian"]),
        ("Banana Bread", "Moist banana bread using ripe bananas", "dessert", 70, ["baking"]),
        ("Thai Green Curry", "Coconut milk based green curry with chicken", "curry", 40, ["thai", "spicy"]),
        ("Shakshuka", "Eggs poached in spiced tomato-pepper sauce", "breakfast", 25, ["breakfast", "eggs"]),
        ("Masoor Dal", "Red lentils tempered with cumin and garlic", "main", 30, ["indian", "lentils"]),
        ("Homemade Pizza Dough", "Basic pizza dough recipe worth remembering", "base", 90, ["baking", "italian"]),
        ("Overnight Oats", "Oats soaked overnight with fruit and honey", "breakfast", 5, ["breakfast", "quick"]),
    ]
    for title, content, dish_type, effort, tags in recipes:
        add(IntentType.RECIPE, title, content, f"{title} — a recipe worth remembering.",
            "cooking", tags, {"dish_name": title, "dish_type": dish_type, "estimated_effort_minutes": effort, "intended_action": "try"},
            group="recipes_to_try")

    # --- Ideas, with varied priority to show off resurfacing cadence ---
    ideas = [
        ("Browser Extension: Thread Summarizer", "An extension that summarizes long email threads", "high"),
        ("Local-First Notes App", "A peer-to-peer syncing notes app, no server needed", "medium"),
        ("Newsletter About AI Failures", "Weekly newsletter on notable AI failure cases", "low"),
        ("Community Fridge App", "Connect neighbors to share surplus food", "medium"),
        ("Personal Finance Dashboard", "One view pulling together all accounts", "high"),
        ("Indie Hackers Podcast", "Interview indie hackers about their first customer", "low"),
        ("Habit Tracker Widget", "A tiny home-screen widget for daily habits", "medium"),
        ("Recipe Cost Calculator", "Estimate cost-per-serving from a recipe's ingredients", "low"),
    ]
    for title, content, priority in ideas:
        add(IntentType.IDEA, title, content, f"{title} — an idea worth developing.",
            "product-ideas", ["idea"], {"idea_statement": content, "priority": priority, "maturity": "captured"},
            group="someday_ideas")

    # --- Learning content, varied completion ---
    learning = [
        ("Neural Networks from Scratch", "video", 0),
        ("System Design Interview Course", "course", 15),
        ("Rust Programming Book", "book", 5),
        ("Kubernetes Fundamentals Article", "article", 100),
        ("SQL Window Functions Tutorial", "article", 40),
        ("Behavioral Economics Podcast", "other", 100),
    ]
    for title, kind, pct in learning:
        add(IntentType.LEARNING_CONTENT, title, f"{title} — learning resource.", f"{title}.",
            "learning", ["learning", kind], {"topic": title, "content_kind": kind, "completion_percent": pct})

    # --- General notes ---
    notes = [
        ("Quote About Patience", "A quote about patience worth remembering"),
        ("Q3 Roadmap Meeting Notes", "Notes from the quarterly roadmap discussion"),
        ("Rent Due Reminder", "Landlord mentioned rent is now due by the 5th"),
        ("Thought About Moving Apartments", "Considering moving closer to work next year"),
        ("Doctor's Sleep Advice", "Doctor recommended a consistent sleep schedule"),
        ("Onboarding Idea from a Conversation", "Idea for improving onboarding, from a chat with a colleague"),
    ]
    for title, content in notes:
        add(IntentType.GENERAL_NOTE, title, content, f"{title}.", "notes", ["note"], {"note_summary": content})

    # --- Reference material: proves the checklist/reference dormant
    # routing without needing a live capture to demonstrate it. ---
    add(IntentType.GENERAL_NOTE, "Packing Checklist",
        "Packing checklist: passport, charger, adapter, meds, headphones",
        "Packing checklist for the next trip.", "packing list", ["travel"],
        {"note_summary": "Packing checklist for next trip"})
    add(IntentType.TASK, "Travel Itinerary",
        "Flight Friday morning, hotel check-in Friday afternoon, conference Saturday-Sunday",
        "Trip itinerary reference.", "travel itinerary", ["travel"],
        {"action_text": "Travel itinerary reference"})

    return items


# Maps each group_key used in build_items() to the Collection it belongs in.
GROUP_COLLECTIONS = {
    "recipes_to_try": ("Recipes to Try", "Dishes worth cooking someday."),
    "fitness_log": ("Fitness Log", "Workouts and activity history."),
    "someday_ideas": ("Someday Ideas", "Ideas worth developing further."),
    "this_week": ("This Week", "Tasks with something due soon."),
}


def main():
    from backend.db.firestore_connection import get_firestore_client
    from backend.repositories.firestore.firestore_item_repository import FirestoreItemRepository
    from backend.repositories.firestore.firestore_lifecycle_repository import FirestoreLifecycleRepository
    from backend.repositories.firestore.firestore_collection_repository import FirestoreCollectionRepository
    from backend.services.collection_service import CollectionService

    client = get_firestore_client()
    print(f"Resetting existing demo data for user_id={DEMO_USER_ID!r}...")
    _reset_demo_account(client)

    item_service = ItemService(FirestoreItemRepository(client))
    lifecycle_service = LifecycleService(FirestoreLifecycleRepository(client))
    collection_service = CollectionService(FirestoreCollectionRepository(client))

    now = utcnow()
    items = build_items(now)

    created = 0
    item_ids_by_group: dict[str, list[str]] = {}
    for item_create, group in items:
        saved_item = item_service.create_item(item_create)
        lifecycle_service.assign_lifecycle(
            item_id=saved_item.item_id,
            user_id=DEMO_USER_ID,
            intent=item_create.intent_type,
            preferences={},
            intent_attributes=item_create.intent_attributes,
            category=item_create.category,
        )
        created += 1
        if group:
            item_ids_by_group.setdefault(group, []).append(saved_item.item_id)

    print(f"Seeded {created} fresh items for the demo account (user_id={DEMO_USER_ID!r}).")

    collections_created = 0
    memberships_created = 0
    for group, item_ids in item_ids_by_group.items():
        name, description = GROUP_COLLECTIONS[group]
        collection = collection_service.create_collection(DEMO_USER_ID, name, description, suggested_by_system=True)
        collections_created += 1
        for item_id in item_ids:
            collection_service.add_item(DEMO_USER_ID, collection.collection_id, item_id, added_by="system")
            memberships_created += 1

    print(f"Created {collections_created} collections with {memberships_created} item memberships.")


if __name__ == "__main__":
    main()
