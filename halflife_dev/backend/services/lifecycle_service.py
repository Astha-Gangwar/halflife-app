import uuid
from datetime import datetime, timedelta
from backend.utils.clock import utcnow
from typing import Dict, Any, Optional
from backend.domain.schemas.lifecycle import LifecycleAssignment
from backend.domain.enums import IntentType, LifecycleState, OutcomeType
from backend.repositories.interfaces.lifecycle_repository import LifecycleRepository
from backend.services.lifecycle_policies import evaluate_policy
from backend.config.lifecycle_policy_config import POLICY_VERSION, DEFAULT_COOLDOWN_DAYS

# Batch 6 §18 outcome-to-lifecycle matrix: which outcomes map to a terminal
# state directly, vs. which require a recalculated schedule (handled below).
_DIRECT_OUTCOME_STATE = {
    OutcomeType.TRIED: LifecycleState.TRIED,
    OutcomeType.COMPLETED: LifecycleState.COMPLETED,
    OutcomeType.MODIFIED: LifecycleState.MODIFIED,
    OutcomeType.NOT_RELEVANT: LifecycleState.NOT_RELEVANT,
    OutcomeType.ARCHIVED: LifecycleState.ARCHIVED,
}

class LifecycleService:
    def __init__(self, lifecycle_repo: LifecycleRepository):
        self.lifecycle_repo = lifecycle_repo

    def assign_lifecycle(
        self,
        item_id: str,
        user_id: str,
        intent: IntentType,
        preferences: Optional[Dict[str, Any]] = None,
        intent_attributes: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None,
    ) -> LifecycleAssignment:
        """
        Determines the appropriate lifecycle state and next review date using
        the per-intent policy (Batch 6 §7-§13). Deterministic and explainable:
        every assignment carries a grounded reason, never an invented date.
        `category` can override the per-intent policy entirely for reference
        material (checklists, itineraries) regardless of intent_type.
        """
        now = utcnow()
        result = evaluate_policy(intent.value, now, intent_attributes or {}, preferences or {}, category)

        assignment = LifecycleAssignment(
            assignment_id=str(uuid.uuid4()),
            user_id=user_id,
            item_id=item_id,
            policy_id=f"{intent.value}_policy",
            policy_version=POLICY_VERSION,
            current_state=result.current_state,
            next_review_date=result.next_review_date,
            eligible_from=result.eligible_from,
            reason=result.reason,
            created_at=now,
            updated_at=now,
        )

        return self.lifecycle_repo.upsert_assignment(assignment)

    def update_item_outcome(
        self,
        item_id: str,
        user_id: str,
        intent: IntentType,
        outcome: OutcomeType,
        remind_at: Optional[datetime] = None,
        preferences: Optional[Dict[str, Any]] = None,
        intent_attributes: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None,
    ) -> LifecycleAssignment:
        """
        Applies a user-recorded outcome to the item's lifecycle assignment
        per the Batch 6 §18 outcome-to-lifecycle matrix. Never invents a
        cooldown or remind date beyond the configured policy defaults.
        """
        existing = self.lifecycle_repo.get_by_item_id(item_id, user_id)
        if existing is None:
            raise ValueError("NO_ACTIVE_LIFECYCLE_ASSIGNMENT: no active lifecycle assignment for this item")

        now = utcnow()

        if outcome == OutcomeType.RESTORED:
            return self.assign_lifecycle(item_id, user_id, intent, preferences, intent_attributes, category)

        if outcome == OutcomeType.REMIND_LATER:
            next_review = remind_at or (now + timedelta(days=DEFAULT_COOLDOWN_DAYS.get(intent.value, 7)))
            existing.current_state = LifecycleState.SCHEDULED_FOR_REVIEW
            existing.next_review_date = next_review
            existing.eligible_from = next_review
            existing.cooldown_until = None
            existing.reason = f"User requested a reminder; rescheduled for {next_review.isoformat()}."
            return self.lifecycle_repo.upsert_assignment(existing)

        if outcome == OutcomeType.DISMISSED:
            cooldown_days = DEFAULT_COOLDOWN_DAYS.get(intent.value, 3)
            cooldown_until = now + timedelta(days=cooldown_days)
            existing.current_state = LifecycleState.DISMISSED
            existing.cooldown_until = cooldown_until
            existing.next_review_date = None
            existing.reason = f"Dismissed; cooldown applied for {cooldown_days} day(s)."
            return self.lifecycle_repo.upsert_assignment(existing)

        new_state = _DIRECT_OUTCOME_STATE.get(outcome)
        if new_state is None:
            raise ValueError(f"INVALID_OUTCOME: unsupported outcome '{outcome}'")

        existing.current_state = new_state
        existing.next_review_date = None
        existing.cooldown_until = None
        existing.reason = f"Outcome recorded: {outcome.value}."
        return self.lifecycle_repo.upsert_assignment(existing)
