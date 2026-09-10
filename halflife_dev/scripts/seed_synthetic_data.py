"""Seed a user's memory library with synthetic demo/test data.

HalfLife doesn't train any model — the agent calls the Gemini API directly
via Google ADK, no fine-tuning involved. "Synthetic data" here means demo
data: a spread of fake memory items across all six intent types so the
capture -> lifecycle -> resurfacing -> feedback loop has something to show
without waiting on real usage history.

Usage:
    python scripts/seed_synthetic_data.py --user-id demo-user

Requires GOOGLE_CLOUD_PROJECT set and Application Default Credentials
available (gcloud auth application-default login) so the Firestore client
can reach your project's database.
"""
import argparse
import os
import sys
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.domain.enums import IntentType, ContentFormat
from backend.domain.schemas.items import SavedItemCreate
from backend.services.item_service import ItemService


def _analysis_id() -> str:
    return f"seed-analysis-{uuid.uuid4().hex[:8]}"


def build_items(user_id: str) -> list[SavedItemCreate]:
    items: list[SavedItemCreate] = []

    def add(intent_type, title, content, summary, category, tags, attributes):
        items.append(SavedItemCreate(
            user_id=user_id,
            original_content=content,
            content_format=ContentFormat.TEXT,
            approved_title=title,
            approved_summary=summary,
            intent_type=intent_type,
            category=category,
            tags=tags,
            intent_attributes=attributes,
            approved_analysis_id=_analysis_id(),
        ))

    # --- Recipes ---
    add(IntentType.RECIPE, "Spaghetti Aglio e Olio",
        "Spaghetti aglio e olio: spaghetti, garlic, olive oil, chili flakes, parsley. 15 min, serves 2.",
        "Quick weeknight pasta with garlic and chili oil.",
        "cooking", ["pasta", "quick", "italian"],
        {"dish_name": "Spaghetti Aglio e Olio", "dish_type": "main", "dietary_tags": ["vegetarian"],
         "estimated_effort_minutes": 15, "servings": 2, "intended_action": "try"})
    add(IntentType.RECIPE, "Chicken Tikka Masala",
        "Chicken tikka masala with marinated chicken, tomato-cream curry sauce, garam masala. ~1hr, serves 4.",
        "Classic creamy chicken curry.",
        "cooking", ["curry", "chicken", "indian"],
        {"dish_name": "Chicken Tikka Masala", "dish_type": "main", "estimated_effort_minutes": 60,
         "servings": 4, "intended_action": "try"})
    add(IntentType.RECIPE, "Banana Bread",
        "Banana bread recipe using 3 ripe bananas, flour, sugar, butter, baking soda. Bake 50 min at 350F.",
        "Moist banana bread for using up ripe bananas.",
        "baking", ["baking", "dessert"],
        {"dish_name": "Banana Bread", "dish_type": "dessert", "estimated_effort_minutes": 70,
         "servings": 8, "intended_action": "reference"})
    add(IntentType.RECIPE, "Thai Green Curry",
        "Thai green curry with coconut milk, green curry paste, chicken, Thai basil, bamboo shoots.",
        "Fragrant coconut curry, medium spice.",
        "cooking", ["thai", "curry", "spicy"],
        {"dish_name": "Thai Green Curry", "dish_type": "main", "estimated_effort_minutes": 40,
         "servings": 3, "intended_action": "try"})
    add(IntentType.RECIPE, "Shakshuka",
        "Shakshuka: eggs poached in spiced tomato-pepper sauce with cumin and paprika. Serve with bread.",
        "One-pan eggs in spiced tomato sauce.",
        "cooking", ["breakfast", "eggs", "mediterranean"],
        {"dish_name": "Shakshuka", "dish_type": "breakfast", "estimated_effort_minutes": 25,
         "servings": 2, "intended_action": "try"})
    add(IntentType.RECIPE, "Masoor Dal",
        "Masoor dal: red lentils cooked with turmeric, tempered with cumin, garlic and ghee.",
        "Simple everyday red lentil dal.",
        "cooking", ["indian", "lentils", "vegetarian"],
        {"dish_name": "Masoor Dal", "dish_type": "main", "dietary_tags": ["vegetarian"],
         "estimated_effort_minutes": 30, "servings": 4, "intended_action": "reference"})

    # --- Learning content ---
    add(IntentType.LEARNING_CONTENT, "Neural Networks from Scratch",
        "Video series building a neural network from scratch in Python without frameworks.",
        "Foundational deep learning video series.",
        "learning", ["ml", "python", "video"],
        {"topic": "Neural networks", "content_kind": "video", "difficulty": "intermediate",
         "learning_goal": "understand backpropagation", "completion_percent": 0})
    add(IntentType.LEARNING_CONTENT, "System Design Interview Course",
        "Online course covering system design interview patterns: load balancing, caching, sharding.",
        "Interview prep course on distributed systems design.",
        "learning", ["system-design", "career"],
        {"topic": "System design", "content_kind": "course", "difficulty": "advanced",
         "learning_goal": "interview prep", "completion_percent": 10})
    add(IntentType.LEARNING_CONTENT, "Rust Programming Book",
        "'The Rust Programming Language' book — ownership, borrowing, lifetimes chapters.",
        "Official Rust language book.",
        "learning", ["rust", "book"],
        {"topic": "Rust", "content_kind": "book", "difficulty": "beginner",
         "learning_goal": "learn a systems language", "completion_percent": 5})
    add(IntentType.LEARNING_CONTENT, "Kubernetes Fundamentals Article",
        "Article explaining pods, deployments, services, and ingress in Kubernetes.",
        "Intro article on core Kubernetes concepts.",
        "learning", ["kubernetes", "devops"],
        {"topic": "Kubernetes", "content_kind": "article", "difficulty": "beginner",
         "completion_percent": 0})
    add(IntentType.LEARNING_CONTENT, "Behavioral Economics Podcast Notes",
        "Notes from a podcast episode on loss aversion and anchoring bias in decision-making.",
        "Podcast notes on cognitive biases.",
        "learning", ["psychology", "podcast"],
        {"topic": "Behavioral economics", "content_kind": "other", "difficulty": "beginner",
         "completion_percent": 100})
    add(IntentType.LEARNING_CONTENT, "SQL Window Functions Tutorial",
        "Tutorial on SQL window functions: ROW_NUMBER, RANK, LAG/LEAD with examples.",
        "Practical SQL window functions tutorial.",
        "learning", ["sql", "database"],
        {"topic": "SQL window functions", "content_kind": "article", "difficulty": "intermediate",
         "completion_percent": 40})

    # --- Ideas ---
    add(IntentType.IDEA, "Browser Extension: Thread Summarizer",
        "Idea: a browser extension that summarizes long email/Slack threads on demand.",
        "Extension idea for summarizing long threads.",
        "product-ideas", ["extension", "productivity"],
        {"idea_statement": "Browser extension that summarizes long threads", "maturity": "exploring",
         "convertible_to_task": False})
    add(IntentType.IDEA, "Local-First Notes App",
        "Weekend hackathon idea: a local-first notes app that syncs peer-to-peer, no server required.",
        "Hackathon idea for a local-first notes app.",
        "product-ideas", ["hackathon", "offline-first"],
        {"idea_statement": "Local-first, peer-to-peer syncing notes app", "maturity": "captured",
         "convertible_to_task": False})
    add(IntentType.IDEA, "Newsletter About AI Failures",
        "Idea for a weekly newsletter collecting notable AI failure cases and what caused them.",
        "Newsletter concept on AI failure case studies.",
        "content-ideas", ["newsletter", "ai"],
        {"idea_statement": "Weekly newsletter on AI failure case studies", "maturity": "exploring",
         "convertible_to_task": False})
    add(IntentType.IDEA, "Community Fridge Sharing App",
        "App idea connecting neighbors to share surplus food via community fridges.",
        "Community food-sharing app concept.",
        "product-ideas", ["community", "social-good"],
        {"idea_statement": "App to coordinate community fridge food sharing", "maturity": "captured",
         "convertible_to_task": False})
    add(IntentType.IDEA, "Personal Finance Dashboard",
        "Idea: a dashboard that pulls all accounts together and shows a single burn-rate number.",
        "Unified personal finance dashboard concept.",
        "product-ideas", ["finance", "dashboard"],
        {"idea_statement": "Single-view personal finance burn-rate dashboard", "maturity": "defined",
         "convertible_to_task": True, "next_question": "Which bank APIs are actually accessible?"})
    add(IntentType.IDEA, "Indie Hackers Podcast",
        "Idea for a podcast interviewing indie hackers about their first paying customer.",
        "Podcast concept on indie hacker origin stories.",
        "content-ideas", ["podcast", "indie-hacking"],
        {"idea_statement": "Podcast on indie hackers' first-customer stories", "maturity": "captured",
         "convertible_to_task": False})

    # --- Tasks ---
    add(IntentType.TASK, "Renew Passport",
        "Need to renew my passport before it expires next month.",
        "Passport renewal, time-sensitive.",
        "admin", ["admin", "urgent"],
        {"action_text": "Renew passport", "priority": "high", "task_status": "open"})
    add(IntentType.TASK, "Book Dentist Appointment",
        "Book a dentist appointment for a routine cleaning.",
        "Routine dental cleaning booking.",
        "health", ["health"],
        {"action_text": "Book dentist appointment", "priority": "medium", "task_status": "open"})
    add(IntentType.TASK, "Submit Tax Documents",
        "Gather and submit tax documents before the filing deadline.",
        "Tax filing paperwork.",
        "admin", ["finance", "deadline"],
        {"action_text": "Submit tax documents", "priority": "high", "task_status": "open"})
    add(IntentType.TASK, "Buy Birthday Gift for Mom",
        "Buy a birthday gift for mom — she mentioned wanting a new gardening set.",
        "Birthday gift shopping.",
        "personal", ["gift", "family"],
        {"action_text": "Buy birthday gift for mom", "priority": "medium", "task_status": "open"})
    add(IntentType.TASK, "Fix Leaking Kitchen Faucet",
        "The kitchen faucet has been dripping — need to fix or call a plumber.",
        "Kitchen faucet repair.",
        "home", ["home-repair"],
        {"action_text": "Fix leaking kitchen faucet", "priority": "medium", "task_status": "open"})
    add(IntentType.TASK, "Call Insurance About Claim",
        "Call the insurance company to follow up on the pending claim status.",
        "Insurance claim follow-up call.",
        "admin", ["finance", "follow-up"],
        {"action_text": "Call insurance about claim", "priority": "medium", "task_status": "open"})

    # --- Activity logs ---
    add(IntentType.ACTIVITY_LOG, "Morning 5K Run",
        "Ran 5km this morning in 28 minutes, felt good.",
        "5km morning run.",
        "fitness", ["running", "cardio"],
        {"activity_type": "running", "completion_status": "completed", "duration_minutes": 28,
         "distance_km": 5})
    add(IntentType.ACTIVITY_LOG, "Leg Day at the Gym",
        "Completed leg day: squats, lunges, leg press. Felt strong on squats.",
        "Leg day strength session.",
        "fitness", ["gym", "strength"],
        {"activity_type": "strength_training", "completion_status": "completed", "duration_minutes": 60})
    add(IntentType.ACTIVITY_LOG, "30-Minute Meditation",
        "Did a 30 minute guided meditation session focused on breathing.",
        "Guided breathing meditation.",
        "wellness", ["meditation", "mindfulness"],
        {"activity_type": "meditation", "completion_status": "completed", "duration_minutes": 30})
    add(IntentType.ACTIVITY_LOG, "Cycled to Work",
        "Cycled 15km to work today instead of driving.",
        "Commute by bike.",
        "fitness", ["cycling", "commute"],
        {"activity_type": "cycling", "completion_status": "completed", "distance_km": 15})
    add(IntentType.ACTIVITY_LOG, "Swimming Session",
        "Swam 20 laps at the pool this evening.",
        "Evening swim session.",
        "fitness", ["swimming"],
        {"activity_type": "swimming", "completion_status": "completed", "duration_minutes": 45})
    add(IntentType.ACTIVITY_LOG, "Yoga Class",
        "Attended a 45 minute vinyasa yoga class.",
        "Vinyasa yoga class.",
        "wellness", ["yoga"],
        {"activity_type": "yoga", "completion_status": "completed", "duration_minutes": 45})

    # --- General notes ---
    add(IntentType.GENERAL_NOTE, "Quote About Patience",
        "Overheard a great quote today: 'patience is not the ability to wait, but to keep a good attitude while waiting.'",
        "A quote about patience worth remembering.",
        "quotes", ["quote", "inspiration"],
        {"note_summary": "Quote about patience while waiting", "topics": ["patience", "quotes"]})
    add(IntentType.GENERAL_NOTE, "Q3 Roadmap Meeting Notes",
        "Meeting notes: Q3 roadmap discussion covered three initiatives, one deprioritized due to headcount.",
        "Notes from the Q3 roadmap planning meeting.",
        "work", ["meeting", "roadmap"],
        {"note_summary": "Q3 roadmap discussion, one initiative deprioritized", "topics": ["roadmap", "planning"]})
    add(IntentType.GENERAL_NOTE, "Onboarding Idea from Priya",
        "Idea from a conversation with Priya about improving the onboarding flow with a progress checklist.",
        "Onboarding improvement idea from a conversation.",
        "work", ["onboarding", "product"],
        {"note_summary": "Onboarding flow improvement idea", "topics": ["onboarding"],
         "people_or_entities": ["Priya"], "suggested_future_intent": "idea"})
    add(IntentType.GENERAL_NOTE, "Rent Due Reminder",
        "Landlord mentioned rent is due by the 5th of each month going forward.",
        "Note on new rent due date.",
        "personal", ["rent", "reminder"],
        {"note_summary": "Rent now due by the 5th each month", "topics": ["rent", "housing"]})
    add(IntentType.GENERAL_NOTE, "Thought About Moving Apartments",
        "Been thinking about moving apartments next year to be closer to work.",
        "Thought about a possible future move.",
        "personal", ["housing", "planning"],
        {"note_summary": "Considering moving apartments next year", "topics": ["housing"]})
    add(IntentType.GENERAL_NOTE, "Doctor's Advice on Sleep",
        "Doctor recommended keeping a consistent sleep schedule and cutting caffeine after 2pm.",
        "Doctor's sleep hygiene advice.",
        "health", ["sleep", "health"],
        {"note_summary": "Doctor's sleep hygiene recommendations", "topics": ["sleep", "health"]})

    return items


def get_item_service() -> ItemService:
    from backend.db.firestore_connection import get_firestore_client
    from backend.repositories.firestore.firestore_item_repository import FirestoreItemRepository
    return ItemService(FirestoreItemRepository(get_firestore_client()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-id", required=True, help="user_id to own the seeded items")
    args = parser.parse_args()

    service = get_item_service()
    items = build_items(args.user_id)

    created = 0
    for item in items:
        service.create_item(item)
        created += 1

    print(f"Seeded {created} synthetic items for user_id={args.user_id!r} into Firestore")


if __name__ == "__main__":
    main()
