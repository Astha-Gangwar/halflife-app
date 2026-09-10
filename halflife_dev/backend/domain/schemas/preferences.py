from pydantic import BaseModel, Field
from datetime import datetime
from backend.utils.clock import utcnow
from typing import Optional, List

class UserPreference(BaseModel):
    preference_id: str
    user_id: str
    timezone: str = "UTC"
    preferred_recipe_days: List[str] = Field(default_factory=list)
    preferred_review_period: Optional[str] = None  # morning, afternoon, evening, null
    max_recipe_effort_minutes: Optional[int] = None
    max_learning_effort_minutes: Optional[int] = None
    revisit_frequency_limit: Optional[int] = None
    uncertain_item_handling: str = "policy_default"  # always_review, policy_default
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    version: int = 1
