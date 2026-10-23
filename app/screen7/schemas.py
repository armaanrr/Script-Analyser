from pydantic import BaseModel, ConfigDict, Field


class AudienceSegment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    segment_type: str = "Secondary"
    target_group: str = "Not established"
    motivations: str = ""
    viewing_context: str = ""
    appeal_barriers: str = ""
    confidence: str = "Medium"


class Women2445Lens(BaseModel):
    model_config = ConfigDict(extra="ignore")
    empowerment_beat: str = ""
    family_resonance: str = ""
    relationship_depth: str = ""
    development_recommendations: list[str] = Field(default_factory=list)


class MoodPhase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    phase: str = "Phase not identified"
    dominant_emotions: list[str] = Field(default_factory=list)
    narrative_payoff: str = ""


class TitleEvaluation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    working_title: str = "Untitled"
    memorability_score: float = Field(default=5.0, ge=0, le=10)
    genre_cultural_fit: str = ""
    strengths: list[str] = Field(default_factory=list)
    alternative_suggestions: list[str] = Field(default_factory=list)


class WorldBuilding(BaseModel):
    model_config = ConfigDict(extra="ignore")
    setting_distinctiveness: str = ""
    social_rules_and_friction: str = ""
    world_consistency: str = ""
    evidence_excerpt: str = ""
    evidence_verified: bool = False


class Screen7AudienceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    project_id: int
    screenplay_version: str = "1.0"
    audience_segments: list[AudienceSegment] = Field(default_factory=list)
    women_development_lens: Women2445Lens = Field(default_factory=Women2445Lens)
    family_suitability_summary: str = ""
    emotional_journey: list[MoodPhase] = Field(default_factory=list)
    title_evaluation: TitleEvaluation = Field(default_factory=TitleEvaluation)
    world_building: WorldBuilding = Field(default_factory=WorldBuilding)
    provider: str = ""
    model: str = ""
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_hit: bool = False
    review_notes: list[str] = Field(default_factory=list)
