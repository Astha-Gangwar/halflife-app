from collections import defaultdict
from typing import Dict, List
from backend.domain.enums import ItemStatus, LifecycleState
from backend.domain.schemas.items import SavedItem
from backend.repositories.interfaces.item_repository import ItemRepository
from backend.utils.clock import utcnow

# current_lifecycle_state values that mean "the user has done something with
# this item" versus it just sitting in the backlog untouched.
ACTED_ON_STATES = {
    LifecycleState.TRIED, LifecycleState.MODIFIED, LifecycleState.COMPLETED,
    LifecycleState.DISMISSED, LifecycleState.NOT_RELEVANT,
}
POSITIVE_STATES = {LifecycleState.TRIED, LifecycleState.COMPLETED}
NEGATIVE_STATES = {LifecycleState.DISMISSED, LifecycleState.NOT_RELEVANT}
STALE_THRESHOLD_DAYS = 14


class InsightsService:
    """Computes Insights-page metrics directly from the items a user already
    has in Firestore — no separate analytics store or event log required,
    since current_lifecycle_state and created_at are already tracked on
    every item."""

    def __init__(self, item_repo: ItemRepository):
        self.item_repo = item_repo

    def get_summary(self, user_id: str) -> Dict:
        items = [
            item for item in self.item_repo.search(user_id, "", limit=1000)
            if item.status != ItemStatus.DELETED
        ]

        total = len(items)
        acted_on = [i for i in items if i.current_lifecycle_state in ACTED_ON_STATES]
        active_backlog = [
            i for i in items
            if i.status == ItemStatus.ACTIVE and i.current_lifecycle_state not in ACTED_ON_STATES
        ]
        now = utcnow()
        stale_backlog = [i for i in active_backlog if (now - i.created_at).days >= STALE_THRESHOLD_DAYS]

        positive = [i for i in acted_on if i.current_lifecycle_state in POSITIVE_STATES]
        negative = [i for i in acted_on if i.current_lifecycle_state in NEGATIVE_STATES]
        resolved = positive + negative

        consumption_rate = round(100 * len(acted_on) / total) if total else 0
        stale_backlog_rate = round(100 * len(stale_backlog) / len(active_backlog)) if active_backlog else 0
        revisit_success_rate = round(100 * len(positive) / len(resolved)) if resolved else None

        return {
            "total_saved": total,
            "consumption_rate": consumption_rate,
            "active_backlog": len(active_backlog),
            "stale_backlog": len(stale_backlog),
            "stale_backlog_rate": stale_backlog_rate,
            "revisit_success_rate": revisit_success_rate,
            "category_performance": self._category_performance(items),
            "behavior_insights": self._behavior_insights(
                total, consumption_rate, len(active_backlog), len(stale_backlog), stale_backlog_rate,
            ),
        }

    def _category_performance(self, items: List[SavedItem]) -> List[Dict]:
        by_category: Dict[str, List[SavedItem]] = defaultdict(list)
        for item in items:
            by_category[item.category or "Uncategorized"].append(item)

        rows = []
        for category, group in by_category.items():
            acted = sum(1 for i in group if i.current_lifecycle_state in ACTED_ON_STATES)
            rows.append({
                "category": category,
                "total": len(group),
                "acted_on_rate": round(100 * acted / len(group)) if group else 0,
            })
        rows.sort(key=lambda r: r["total"], reverse=True)
        return rows[:5]

    def _behavior_insights(
        self, total: int, consumption_rate: int, active_backlog: int, stale_count: int, stale_rate: int,
    ) -> List[str]:
        if total == 0:
            return ["Nothing saved yet — capture something to start seeing insights here."]

        insights = [f"You've acted on {consumption_rate}% of everything you've saved."]
        if stale_count > 0:
            insights.append(
                f"{stale_count} item{'s' if stale_count != 1 else ''} in your backlog "
                f"{'have' if stale_count != 1 else 'has'} sat untouched for {STALE_THRESHOLD_DAYS}+ days "
                f"({stale_rate}% of your active backlog)."
            )
        if active_backlog > 0:
            insights.append(f"You currently have {active_backlog} item{'s' if active_backlog != 1 else ''} still active in your backlog.")
        return insights
