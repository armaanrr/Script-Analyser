from typing import Literal, Optional, List
from pydantic import BaseModel, ConfigDict, Field


class RewriteTask(BaseModel):
    model_config = ConfigDict(extra="ignore")
    priority: Literal["High", "Medium", "Low"] = "Medium"
    issue_evidence: str = Field(default="", description="Brief explanation of the script issue")
    evidence_excerpt: str = Field(default="", description="Short exact quote from the screenplay supporting the issue")
    evidence_verified: bool = False
    proposed_action: str = Field(default="", description="Clear rewrite instruction")
    success_criteria: str = Field(default="", description="How to verify the fix works")
    owner: str = Field(default="Writer", description="Assigned role, e.g., Writer, Producer")
    status: Literal["Open", "In Progress", "Resolved"] = "Open"


class EpisodeDiagnostic(BaseModel):
    model_config = ConfigDict(extra="ignore")
    episode_number: int = Field(ge=1)
    episode_title: str = "Untitled Episode"
    scene_range: str = Field(default="Location not identified", description="Source location; do not invent scene numbers")
    opening_hook: str = ""
    hook_rating: Literal["Strong", "Moderate", "Weak"] = "Moderate"
    conflict_progression: str = ""
    emotional_shift: str = ""
    ending_cliffhanger: str = ""
    cliffhanger_rating: Literal["Strong", "Moderate", "Weak"] = "Moderate"
    continuity_payoffs: str = ""
    estimated_word_count: int = 0
    estimated_runtime_seconds: int = 0
    exceeds_max_runtime: bool = False
    rewrite_task: Optional[RewriteTask] = None


class Screen5DiagnosticsResponse(BaseModel):
    project_id: int
    screenplay_version: str = "1.0"
    total_episodes_detected: int
    producer_selected_episode_count: int = 1
    recommended_episode_count: int = 1
    recommendation_reason: str = ""
    max_episode_duration_seconds: int = 180
    episodes_over_runtime_limit: int = 0
    episodes: List[EpisodeDiagnostic]
    provider: str = ""
    model: str = ""
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_hit: bool = False
    review_notes: List[str] = Field(default_factory=list)
