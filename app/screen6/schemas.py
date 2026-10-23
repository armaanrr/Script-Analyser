from typing import List
from pydantic import BaseModel, ConfigDict, Field


class CharacterProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = "Unnamed character"
    role: str = "Supporting"
    goals_external: str = ""
    internal_need: str = ""
    fear_and_stakes: str = ""
    character_arc: str = ""
    agency_level: str = "Medium"
    evidence_excerpt: str = ""
    evidence_verified: bool = False


class RelationshipShift(BaseModel):
    model_config = ConfigDict(extra="ignore")
    characters: str = "Unspecified characters"
    relationship_type: str = "Other"
    power_balance: str = ""
    key_conflict: str = ""
    evidence_excerpt: str = ""
    evidence_verified: bool = False


class EmotionalBeat(BaseModel):
    model_config = ConfigDict(extra="ignore")
    episode_scene: str = "Location not identified"
    emotion_type: str = "Unspecified"
    quote_excerpt: str = ""
    impact_rationale: str = ""
    evidence_verified: bool = False


class ConsistencyCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    character_or_relation: str = "Unspecified"
    issue_type: str = "Review"
    scene_reference: str = "Location not identified"
    description: str = ""
    evidence_excerpt: str = ""
    evidence_verified: bool = False


class CastingRequirement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    character_name: str = "Unspecified character"
    age_range: str = "Not specified by script"
    language_performance: str = ""
    key_traits: List[str] = Field(default_factory=list)


class Screen6CharactersResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    project_id: int
    screenplay_version: str = "1.0"
    character_profiles: List[CharacterProfile] = Field(default_factory=list)
    relationships: List[RelationshipShift] = Field(default_factory=list)
    emotional_beats: List[EmotionalBeat] = Field(default_factory=list)
    consistency_checks: List[ConsistencyCheck] = Field(default_factory=list)
    casting_requirements: List[CastingRequirement] = Field(default_factory=list)
    provider: str = ""
    model: str = ""
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_hit: bool = False
    review_notes: List[str] = Field(default_factory=list)
