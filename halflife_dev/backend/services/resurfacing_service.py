import uuid
from typing import List
from datetime import datetime
from backend.utils.clock import utcnow
from backend.domain.schemas.lifecycle import ResurfacingCandidate
from backend.domain.enums import LifecycleState, ResurfacingStatus
from backend.repositories.interfaces.lifecycle_repository import LifecycleRepository
from backend.repositories.interfaces.resurfacing_repository import ResurfacingRepository
from backend.config.lifecycle_policy_config import RANKING_WEIGHTS, DEFAULT_REVISIT_LIMIT


class ResurfacingService:
    def __init__(self, lifecycle_repo: LifecycleRepository, resurfacing_repo: ResurfacingRepository = None):
        self.lifecycle_repo = lifecycle_repo
        self.resurfacing_repo = resurfacing_repo

    def get_revisit_candidates(self, user_id: str, limit: int = DEFAULT_REVISIT_LIMIT) -> List[ResurfacingCandidate]:
        """
        Batch 6 §14 pipeline: retrieve -> evaluate eligibility -> apply
        exclusions -> create candidate -> rank -> select. The lifecycle
        repository's get_revisit_candidates already applies the state filter
        (EL-005); this stage applies timing (EL-004), cooldown (EL-006), and
        creates a persisted, ranked ResurfacingCandidate per eligible item.
        """
        assignments = self.lifecycle_repo.get_revisit_candidates(user_id, limit=limit * 3)

        now = utcnow()
        eligible = []
        for assignment in assignments:
            if assignment.cooldown_until and assignment.cooldown_until > now:
                continue  # EL-006: cooldown active
            if assignment.next_review_date and assignment.next_review_date > now:
                continue  # EL-004: not yet eligible
            eligible.append(assignment)

        ranked = sorted(eligible, key=self._rank_score, reverse=True)[:limit]

        candidates = []
        for assignment in ranked:
            candidate = ResurfacingCandidate(
                resurfacing_id=str(uuid.uuid4()),
                user_id=user_id,
                item_id=assignment.item_id,
                assignment_id=assignment.assignment_id,
                status=ResurfacingStatus.SELECTED,
                eligibility_reason_code=self._reason_code(assignment.reason),
                supporting_facts={"reason": assignment.reason},
                rank_score=self._rank_score(assignment),
                rank_factors={"age_since_eligible_days": self._age_days(assignment, now)},
                eligible_at=assignment.eligible_from or assignment.next_review_date or now,
                selected_at=now,
                created_at=now,
            )
            if self.resurfacing_repo is not None:
                candidate = self.resurfacing_repo.create_candidate(candidate)
            candidates.append(candidate)

        return candidates

    def record_resurfacing(self, resurfacing_id: str, user_id: str) -> ResurfacingCandidate:
        if self.resurfacing_repo is None:
            raise ValueError("Resurfacing repository not configured")
        candidate = self.resurfacing_repo.update_status(
            resurfacing_id, user_id, ResurfacingStatus.PRESENTED.value, presented_at=utcnow()
        )
        assignment = self.lifecycle_repo.get_by_item_id(candidate.item_id, user_id)
        if assignment is not None:
            assignment.current_state = LifecycleState.RESURFACED
            self.lifecycle_repo.upsert_assignment(assignment)
        return candidate

    def _age_days(self, assignment, now: datetime) -> float:
        anchor = assignment.eligible_from or assignment.next_review_date or assignment.created_at
        return max((now - anchor).total_seconds() / 86400.0, 0.0)

    def _reason_code(self, reason: str) -> str:
        if not reason:
            return "MANUAL_REVISIT"
        for code in (
            "PREFERRED_RECIPE_DAY", "EXPLICIT_REVIEW_DATE", "TASK_DUE_SOON", "TASK_OVERDUE",
            "LEARNING_ITEM_AGED", "IDEA_INACTIVE", "RELATED_NEW_MEMORY",
            "ACTIVITY_COMPARISON_AVAILABLE", "LONG_INACTIVITY_REVIEW",
        ):
            if code in reason:
                return code
        return "MANUAL_REVISIT"

    def _rank_score(self, assignment) -> float:
        score = RANKING_WEIGHTS["policy_eligibility"]
        now = utcnow()
        if assignment.next_review_date and assignment.next_review_date <= now:
            score += RANKING_WEIGHTS["explicit_due_or_requested_date"] if "TASK" in (assignment.reason or "") else 0
        score += min(self._age_days(assignment, now), 30) * (RANKING_WEIGHTS["age_since_save_or_action"] / 30.0)
        return score
