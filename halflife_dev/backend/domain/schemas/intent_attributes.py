from typing import Optional, List
from pydantic import BaseModel, Field
from backend.domain.enums import SourceType, IntentType


class Ingredient(BaseModel):
    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    preparation: Optional[str] = None
    source: SourceType


class RecipeAttributes(BaseModel):
    dish_name: Optional[str] = None
    ingredients: List[Ingredient] = Field(default_factory=list)
    cooking_methods: List[str] = Field(default_factory=list)
    dish_type: Optional[str] = None
    dietary_tags: List[str] = Field(default_factory=list)
    estimated_effort_minutes: Optional[int] = None
    servings: Optional[float] = None
    source_url: Optional[str] = None
    intended_action: str = "unknown"  # try, reference, modify, compare, unknown


class LearningContentAttributes(BaseModel):
    topic: str
    content_kind: str  # article, video, notes, course, book, other
    source_url: Optional[str] = None
    creator_or_author: Optional[str] = None
    estimated_effort_minutes: Optional[int] = None
    difficulty: str = "unknown"  # beginner, intermediate, advanced, unknown
    learning_goal: Optional[str] = None
    completion_percent: float = 0
    key_topics: List[str] = Field(default_factory=list)


class IdeaAttributes(BaseModel):
    idea_statement: str
    theme: Optional[str] = None
    purpose: Optional[str] = None
    maturity: str = "captured"  # captured, exploring, defined, actionable
    priority: str = "unspecified"  # low, medium, high, unspecified
    next_question: Optional[str] = None
    convertible_to_task: bool = False
    supporting_points: List[str] = Field(default_factory=list)


class TaskAttributes(BaseModel):
    action_text: str
    due_at: Optional[str] = None
    due_date_source: Optional[SourceType] = None
    priority: str = "unspecified"  # low, medium, high, unspecified
    task_status: str = "open"  # open, in_progress, completed, cancelled
    steps: List[str] = Field(default_factory=list)
    completion_note: Optional[str] = None
    completed_at: Optional[str] = None


class ExerciseEntry(BaseModel):
    name: str
    sets: Optional[int] = None
    repetitions: Optional[int] = None
    weight_kg: Optional[float] = None
    distance_km: Optional[float] = None
    duration_minutes: Optional[float] = None


class ActivityLogAttributes(BaseModel):
    activity_type: str
    activity_at: Optional[str] = None
    completion_status: str = "unknown"  # planned, completed, partial, unknown
    duration_minutes: Optional[float] = None
    distance_km: Optional[float] = None
    exercises: List[ExerciseEntry] = Field(default_factory=list)
    notes: Optional[str] = None
    source: SourceType = SourceType.EXPLICIT


class GeneralNoteAttributes(BaseModel):
    note_summary: str
    topics: List[str] = Field(default_factory=list)
    people_or_entities: List[str] = Field(default_factory=list)
    reference_dates: List[str] = Field(default_factory=list)
    suggested_future_intent: Optional[IntentType] = None


INTENT_ATTRIBUTE_MODELS = {
    IntentType.RECIPE: RecipeAttributes,
    IntentType.LEARNING_CONTENT: LearningContentAttributes,
    IntentType.IDEA: IdeaAttributes,
    IntentType.TASK: TaskAttributes,
    IntentType.ACTIVITY_LOG: ActivityLogAttributes,
    IntentType.GENERAL_NOTE: GeneralNoteAttributes,
}


def parse_intent_attributes(intent_type: IntentType, raw: dict) -> Optional[BaseModel]:
    """Validate and construct the typed attributes model matching intent_type.

    Returns None for IntentType.UNKNOWN, which has no attribute schema.
    """
    model = INTENT_ATTRIBUTE_MODELS.get(intent_type)
    if model is None:
        return None
    return model.model_validate(raw or {})
