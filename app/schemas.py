"""Pydantic models.

Three groups:
  1. ConceptInput             - what a person submits (Screen 1 intake panel)
  2. ConceptAnalysis (+parts) - what the LLM must return (structured output)
  3. TractionRecord / ScoreResult - filled by the BACKEND, never by the LLM
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field

Source = Literal["knowledge_base", "model_general_knowledge"]


# ---------- 1. Intake ----------
class ConceptInput(BaseModel):
    working_title: str = Field(min_length=2, max_length=120)
    logline: str = Field(min_length=20, max_length=500)
    synopsis: str = Field(min_length=100)
    dramatic_mechanism: str = Field(min_length=20)
    characters_setup: str = Field(min_length=20)
    likely_twists: str = ""
    intended_format: str = "Vertical micro-drama, ~30 short episodes"
    submitting_owner: str = Field(min_length=2, max_length=120)


# ---------- 2. LLM output schema (no defaults: keeps provider schemas strict) ----------
class Similarity(BaseModel):
    reference_title: str
    source: Source
    overlap_type: Literal["premise", "dramatic_mechanism", "character_setup", "twist", "other"]
    similarity_detail: str
    difference_detail: str


class OriginalityAssessment(BaseModel):
    summary: str
    similarities: list[Similarity]
    distinguishing_elements: list[str]
    uncertainties: list[str]


class ComparableTitle(BaseModel):
    title: str
    source: Source
    why_comparable: str


class Taxonomy(BaseModel):
    primary_category: str
    secondary_category: Optional[str]
    primary_genre: str
    secondary_genre: Optional[str]
    subgenre: str
    tropes: list[str]
    clarity_note: str


class AudienceSegment(BaseModel):
    label: str
    age_band: str
    gender_focus: str
    motivations: list[str]
    viewing_context: str
    appeal_barriers: list[str]
    confidence: Literal["low", "medium", "high"]
    rationale: str


class DevelopmentIdea(BaseModel):
    focus: Literal["emotional_relevance", "agency", "relationships", "ambition",
                   "family_resonance", "empowerment"]
    idea: str
    originality_safeguard: str   # how to apply the idea without making the concept generic


class AudienceLens(BaseModel):
    primary_segments: list[AudienceSegment]
    secondary_segments: list[AudienceSegment]
    development_ideas: list[DevelopmentIdea]   # 2-4


class MicroDramaViability(BaseModel):
    verdict: Literal["strong", "moderate", "weak", "uncertain"]
    rationale: str
    escalation_beats: list[str]
    uncertainties: list[str]


DimensionKey = Literal["originality", "comparables", "taxonomy",
                       "women_24_45_development", "audience_id", "micro_drama_engine"]


class DimensionRating(BaseModel):
    dimension_key: DimensionKey
    rating: Optional[float]      # 0-10; null when evidence is insufficient (never guess)
    rationale: str
    evidence_basis: str          # which part of the submission supports this rating


class ConceptAnalysis(BaseModel):
    originality: OriginalityAssessment
    comparable_titles: list[ComparableTitle]
    taxonomy: Taxonomy
    audience: AudienceLens
    micro_drama: MicroDramaViability
    ratings: list[DimensionRating]


# ---------- 3. Backend-owned results ----------
class TractionRecord(BaseModel):
    title: str
    available: bool
    reason: Optional[str] = None            # why unavailable
    launch_hours_streamed: Optional[float] = None
    lifetime_hours_streamed: Optional[float] = None
    unique_users: Optional[int] = None
    stickiness: Optional[float] = None
    completion_rate: Optional[float] = None
    metric_definitions: Optional[str] = None
    reporting_window: Optional[str] = None
    source: Optional[str] = None
    extracted_on: Optional[str] = None


class DimensionScore(BaseModel):
    key: str
    label: str
    weight: int
    rating: Optional[float]
    points: Optional[float]
    status: Literal["rated", "provisional", "incomplete"]
    note: Optional[str] = None


class ScoreResult(BaseModel):
    dimensions: list[DimensionScore]
    total: Optional[float]                  # None when any rating is incomplete
    points_so_far: float
    status: Literal["complete", "provisional", "incomplete"]
    status_reason: str


class DecisionIn(BaseModel):
    decision: Literal["approve_to_screenplay", "revise_concept",
                      "hold_for_research", "reject_concept"]
    rationale: str = Field(min_length=10)
