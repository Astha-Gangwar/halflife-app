from abc import ABC, abstractmethod
from typing import Optional
from backend.domain.schemas.preferences import UserPreference

class PreferenceRepository(ABC):
    @abstractmethod
    def get_by_user_id(self, user_id: str) -> Optional[UserPreference]:
        pass

    @abstractmethod
    def upsert(self, preference: UserPreference) -> UserPreference:
        pass
