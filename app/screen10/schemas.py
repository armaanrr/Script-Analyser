from typing import Any, Literal
from pydantic import BaseModel, Field

ConceptDecision = Literal["approve_to_screenplay", "revise_concept", "hold_for_research", "reject_concept"]
ScreenplayDecision = Literal["approve_screenplay", "revise_screenplay", "hold_for_review", "reject_screenplay"]

class DecisionRequest(BaseModel):
    decision_type: Literal["concept", "screenplay"]
    decision: str
    rationale: str = Field(min_length=10, max_length=5000)
    reviewer_name: str = Field(min_length=1, max_length=120)
    reviewer_role: Literal["owner", "producer", "director", "writer"]
    version_label: str = ""

class ChecklistRequest(BaseModel):
    reviewer_name: str = Field(min_length=1, max_length=120)
    reviewer_role: Literal["owner", "producer", "director", "writer"]
    items: dict[str, bool | str | None]

class OverrideRequest(BaseModel):
    field_key: str = Field(min_length=1, max_length=100)
    original_value: str = Field(max_length=5000)
    adjusted_value: str = Field(max_length=5000)
    rationale: str = Field(min_length=10, max_length=5000)
    reviewer_name: str = Field(min_length=1, max_length=120)
    reviewer_role: Literal["owner", "producer", "director", "writer"]

class LearningRequest(BaseModel):
    source_name: str = Field(min_length=1, max_length=200)
    reporting_window: str = Field(min_length=1, max_length=200)
    extracted_at: str = Field(min_length=1, max_length=80)
    metrics: dict[str, Any] = Field(default_factory=dict)
    note: str = ""
    created_by: str = Field(min_length=1, max_length=120)
