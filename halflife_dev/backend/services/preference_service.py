import uuid
from datetime import datetime
from backend.utils.clock import utcnow
from typing import Optional
from backend.domain.schemas.preferences import UserPreference
from backend.repositories.interfaces.preference_repository import PreferenceRepository

class PreferenceService:
    def __init__(self, preference_repo: PreferenceRepository):
        self.preference_repo = preference_repo

    def get_preferences(self, user_id: str) -> UserPreference:
        existing = self.preference_repo.get_by_user_id(user_id)
        if existing is not None:
            return existing
        # No preferences set yet: return system defaults without persisting them,
        # so defaults stay clearly distinguishable from explicit user choices.
        return UserPreference(preference_id=str(uuid.uuid4()), user_id=user_id)

    def update_preferences(self, user_id: str, **patch) -> UserPreference:
        existing = self.preference_repo.get_by_user_id(user_id)
        if existing is None:
            existing = UserPreference(preference_id=str(uuid.uuid4()), user_id=user_id)
        for key, value in patch.items():
            if value is not None and hasattr(existing, key):
                setattr(existing, key, value)
        existing.updated_at = utcnow()
        return self.preference_repo.upsert(existing)
