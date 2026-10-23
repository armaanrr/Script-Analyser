from typing import Literal, List
from pydantic import BaseModel, Field


class FlaggedScene(BaseModel):
    episode_id: str = Field(description="Episode and/or scene location as shown in the screenplay")
    quote_excerpt: str = Field(description="Short verbatim quote from the screenplay")
    issue_description: str = Field(description="Why the scene requires editorial review")
    evidence_verified: bool = False


class GateCheck(BaseModel):
    key: str
    label: str
    status: Literal["Pass", "Review Required", "Blocked", "Incomplete"]
    summary: str
    flagged_scenes: List[FlaggedScene] = Field(default_factory=list)


class RomanceMoment(BaseModel):
    episode_scene: str = Field(description="Episode/scene location from the source")
    quote_excerpt: str = Field(description="Short verbatim dialogue/action from the screenplay")
    emotional_punch: str = Field(description="Why this moment lands emotionally")
    evidence_verified: bool = False


class IntensityMeter(BaseModel):
    key: str
    label: str
    score: float = Field(ge=0.0, le=10.0, description="Score out of 10")
    supporting_beats: List[str] = Field(default_factory=list)


class HighRomanceMeter(IntensityMeter):
    top_moments: List[RomanceMoment] = Field(default_factory=list, description="Up to 5 evidence-based high-romance moments")


class Screen4GatesResponse(BaseModel):
    project_id: int
    screenplay_version: str = "1.0"
    overall_gate_status: Literal["Pass", "Review Required", "Blocked"]
    gates: List[GateCheck]
    cringe_meter: IntensityMeter
    humiliation_meter: IntensityMeter
    high_romance_meter: HighRomanceMeter
    provider: str = ""
    model: str = ""
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_hit: bool = False
    review_notes: List[str] = Field(default_factory=list)
