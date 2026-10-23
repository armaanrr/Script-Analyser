from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class CastRoleItem(BaseModel):
    name: str = Field(description="Character or role name")
    role_tier: Literal["Principal Lead", "Supporting", "Featured Extra", "Crowd / Background"]
    scene_count_estimate: int
    costume_changes: int = 1
    key_scenes: str = Field(description="Comma-separated scene references")
    notes: str = Field(description="Special demands, props, or stunt requirements")


class LocationItem(BaseModel):
    name: str = Field(description="Location name, e.g., Mirza Bungalow Lawn")
    setting_type: Literal["INT", "EXT", "INT/EXT"]
    lighting: Literal["DAY", "NIGHT", "DAY/NIGHT"]
    scene_references: List[str] = Field(default_factory=list)
    complexity: Literal["Low", "Medium", "High"]
    practical_considerations: str


class SceneComplexityStats(BaseModel):
    total_scenes: int
    interior_scenes: int
    exterior_scenes: int
    day_scenes: int
    night_scenes: int
    high_complexity_scenes: int
    medium_complexity_scenes: int
    low_complexity_scenes: int


class ShootingDayFormula(BaseModel):
    total_scenes: int
    unique_locations_count: int
    high_complexity_count: int
    base_scenes_per_day: float = Field(default=4.5, description="Industry standard for vertical drama")
    base_days: float
    location_move_penalty_days: float
    complexity_buffer_days: float
    total_estimated_shooting_days: float
    visible_formula: str = Field(description="Display formula explaining the arithmetic")


class RewritePlanTask(BaseModel):
    task_id: str
    priority: Literal["High", "Medium", "Low"]
    target_scenes: str
    issue_identified: str
    proposed_rewrite: str
    expected_impact: str
    owner: str = "Writer"
    status: Literal["Open", "In Progress", "Resolved"] = "Open"


class VersionDiffItem(BaseModel):
    current_version: int
    comparison_summary: str
    resolved_from_previous: List[str] = Field(default_factory=list)
    new_or_modified_beats: List[str] = Field(default_factory=list)
    production_impact_changes: List[str] = Field(default_factory=list)


class UpdateTaskStatusRequest(BaseModel):
    status: Literal["Open", "In Progress", "Resolved"]
    owner: Optional[str] = None


class Screen9ProductionResponse(BaseModel):
    project_id: int
    screenplay_version: int
    complexity_stats: SceneComplexityStats
    shooting_estimate: ShootingDayFormula
    cast_breakdown: List[CastRoleItem]
    location_breakdown: List[LocationItem]
    rewrite_plan: List[RewritePlanTask]
    version_comparison: VersionDiffItem
    provider: Optional[str] = None
    model: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cache_hit: bool = False
    review_notes: List[str] = Field(default_factory=list)