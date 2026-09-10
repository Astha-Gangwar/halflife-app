from typing import Optional
from datetime import datetime
from backend.utils.clock import utcnow, normalize_firestore_datetimes
from backend.repositories.interfaces.preference_repository import PreferenceRepository
from backend.domain.schemas.preferences import UserPreference

COLLECTION = "preferences"


class FirestorePreferenceRepository(PreferenceRepository):
    def __init__(self, db):
        self.db = db

    def get_by_user_id(self, user_id: str) -> Optional[UserPreference]:
        query = self.db.collection(COLLECTION).where("user_id", "==", user_id).limit(1).stream()
        snap = next(iter(query), None)
        if snap is None:
            return None
        return self._to_domain(snap.to_dict())

    def upsert(self, preference: UserPreference) -> UserPreference:
        col = self.db.collection(COLLECTION)
        query = col.where("user_id", "==", preference.user_id).limit(1).stream()
        existing_snap = next(iter(query), None)

        if existing_snap is not None:
            data = existing_snap.to_dict()
            updates = {
                "timezone": preference.timezone,
                "preferred_recipe_days": list(preference.preferred_recipe_days),
                "preferred_review_period": preference.preferred_review_period,
                "max_recipe_effort_minutes": preference.max_recipe_effort_minutes,
                "max_learning_effort_minutes": preference.max_learning_effort_minutes,
                "revisit_frequency_limit": preference.revisit_frequency_limit,
                "uncertain_item_handling": preference.uncertain_item_handling,
                "updated_at": utcnow(),
                "version": data.get("version", 1) + 1,
            }
            existing_snap.reference.update(updates)
            data.update(updates)
            return self._to_domain(data)
        else:
            doc = {
                "preference_id": preference.preference_id,
                "user_id": preference.user_id,
                "timezone": preference.timezone,
                "preferred_recipe_days": list(preference.preferred_recipe_days),
                "preferred_review_period": preference.preferred_review_period,
                "max_recipe_effort_minutes": preference.max_recipe_effort_minutes,
                "max_learning_effort_minutes": preference.max_learning_effort_minutes,
                "revisit_frequency_limit": preference.revisit_frequency_limit,
                "uncertain_item_handling": preference.uncertain_item_handling,
                "created_at": preference.created_at,
                "updated_at": preference.updated_at,
                "version": preference.version,
            }
            col.document(preference.preference_id).set(doc)
            return self._to_domain(doc)

    def _to_domain(self, data: dict) -> UserPreference:
        data = normalize_firestore_datetimes(data)
        return UserPreference(
            preference_id=data["preference_id"],
            user_id=data["user_id"],
            timezone=data["timezone"],
            preferred_recipe_days=data.get("preferred_recipe_days") or [],
            preferred_review_period=data.get("preferred_review_period"),
            max_recipe_effort_minutes=data.get("max_recipe_effort_minutes"),
            max_learning_effort_minutes=data.get("max_learning_effort_minutes"),
            revisit_frequency_limit=data.get("revisit_frequency_limit"),
            uncertain_item_handling=data["uncertain_item_handling"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            version=data["version"],
        )
