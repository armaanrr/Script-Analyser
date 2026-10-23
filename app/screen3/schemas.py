from typing import List, Optional
from pydantic import BaseModel, Field


class DimensionScore(BaseModel):
    key: str
    label: str
    weight: int
    rating: Optional[float] = Field(default=None, ge=0, le=10, description="Rating from 0 to 10")
    calculated_points: Optional[float] = Field(default=None, description="Backend calculated: (rating / 10) * weight")
    evidence_excerpt: str = Field(default="", description="Verbatim script excerpt verified against source")
    location_reference: str = Field(default="", description="Episode, scene, or page reference")
    rationale: str = Field(default="", description="Analytical rationale for the rating")
    is_complete: bool = True


class ScorecardResponse(BaseModel):
    project_id: int
    screenplay_version: str
    total_score: float = Field(..., description="Weighted sum out of 100")
    is_complete: bool = Field(..., description="False if required ratings/evidence are missing")
    dimensions: List[DimensionScore]
    human_override: Optional[dict] = None
    provider: str = ""
    model: str = ""
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cache_hit: bool = False
    overall_summary: str = ""
    strongest_dimensions: List[str] = Field(default_factory=list)
    priority_improvements: List[str] = Field(default_factory=list)
