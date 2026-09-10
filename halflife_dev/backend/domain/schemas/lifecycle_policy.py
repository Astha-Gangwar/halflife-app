from typing import Any, List
from pydantic import BaseModel, Field
from backend.domain.enums import IntentType

class RuleDefinition(BaseModel):
    rule_id: str
    description: str
    field: str
    operator: str  # eq, neq, gt, gte, lt, lte, in, not_in, exists
    value: Any
    outcome: str
    priority: int = 0

class LifecyclePolicyDefinition(BaseModel):
    policy_id: str
    version: str
    supported_intents: List[IntentType]
    required_inputs: List[str] = Field(default_factory=list)
    eligibility_rules: List[RuleDefinition] = Field(default_factory=list)
    exclusion_rules: List[RuleDefinition] = Field(default_factory=list)
    feedback_type_after_action: str | None = None
    active: bool = True
