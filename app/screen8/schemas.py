from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class PromoScene(BaseModel):
    scene_ref: str = Field(description="Exact scene reference, e.g., Scene 8, Scene 28, Scene 41")
    context: str = Field(description="Context and narrative setup of the scene")
    emotional_punch: str = Field(description="Why this scene grabs audience attention")
    intended_use: str = Field(description="e.g., Main Trailer Hook, Pre-roll Teaser, Climax Reveal")
    spoiler_risk: Literal["Low", "Medium", "High"] = "Low"


class VerbatimDialogue(BaseModel):
    quote: str = Field(description="Verbatim dialogue quote from the screenplay")
    speaker: str = Field(description="Character who delivers the dialogue")
    scene_ref: str = Field(description="Exact scene where dialogue occurs")
    context: str = Field(description="Scene context")
    emotional_punch: str = Field(description="Emotional impact of the line")
    spoiler_risk: Literal["Low", "Medium", "High"] = "Low"


class SeasonStrategy(BaseModel):
    recommendation: Literal["Standalone Conclusion", "Season 2 Viable", "Hybrid Strategy"]
    resolved_arcs: List[str] = Field(default_factory=list, description="Story arcs concluded in this draft")
    open_threads: List[str] = Field(default_factory=list, description="Unresolved tensions or lingering conflicts")
    sequel_engine: str = Field(description="Core narrative motor driving a potential Season 2")
    ending_payoff_rationale: str = Field(description="Why the ending satisfies the viewer while sustaining franchise value")


class CastingContext(BaseModel):
    confirmed_genre: str
    content_positioning: str
    role_brief: str
    language_demands: str
    audience_expectation: str


class CandidateComparison(BaseModel):
    candidate_name: str
    target_role: str
    role_fit_analysis: str
    positioning_fit_analysis: str
    trade_offs_and_alternatives: str
    confidence_level: Literal["High", "Medium", "Review Required"] = "High"
    review_prompt: str = Field(description="Review prompt for producer consideration")
    current_decision: Optional[str] = "Under Review"
    decision_rationale: Optional[str] = ""
    decided_by: Optional[str] = None


class CastingDecisionRequest(BaseModel):
    candidate_name: str
    target_role: str
    decision: Literal["Shortlist", "Research Further", "Do Not Shortlist", "Override"]
    rationale: str = Field(min_length=10, description="Minimum 10 characters rationale")
    decided_by: str = "Producer"


class CastingDecisionResponse(BaseModel):
    status: str
    message: str
    candidate_name: str
    decision: str
    rationale: str
    decided_by: str


class Screen8PromoResponse(BaseModel):
    project_id: int
    screenplay_version: str = "1.0"
    provider: Optional[str] = None
    model: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cache_hit: bool = False
    review_notes: List[str] = Field(default_factory=list)
    promo_scenes: List[PromoScene]
    verbatim_dialogues: List[VerbatimDialogue]
    season_strategy: SeasonStrategy
    casting_context: CastingContext
    candidates: List[CandidateComparison]