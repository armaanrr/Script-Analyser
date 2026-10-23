"""AI genre/subgenre classification: output schema + prompt. No defaults in the schema (strict providers)."""
from typing import Literal, Optional
from pydantic import BaseModel, Field

PROMPT_VERSION = "classification-v1"
MODULE = "classification"


class EvidenceItem(BaseModel):
    episode_id: str                 # e.g. "E03", taken from the [E03] markers
    scene_id: Optional[str]         # e.g. "E03-S02" if a scene marker applies, else null
    quote: str                      # verbatim from the screenplay, max 25 words, no ellipses
    supports: str                   # what this evidence shows about genre / conflict / tone


class GenreAssessment(BaseModel):
    primary_genre: str
    secondary_genre_elements: list[str]
    subgenre: str
    confidence: Literal["low", "medium", "high"]
    ambiguity_note: Optional[str]
    story_engine: str
    central_conflict: str
    relationship_dynamics: str
    tone: str
    narrative_patterns: list[str]
    alternative_classifications: list[str]
    evidence: list[EvidenceItem] = Field(description="4 to 8 items spanning several episodes")


SYSTEM = """You are a development analyst for Rocket Reels, a vertical-drama OTT platform.
You are given a COMPLETED screenplay (a series of short episodes) and must classify it independently.

Rules:
- Classify from the screenplay text only. You are NOT told what genre the script claims; never guess it.
- primary_genre and subgenre: short, conventional labels (1-3 words). secondary_genre_elements: 0-3 labels.
- Explain using story engine, central conflict, relationship dynamics, tone and narrative patterns.
- Give 4-6 evidence items spread across several different episodes. Each quote must be copied
  VERBATIM from the text (max 25 words, no ellipses, no paraphrase, keep the original script/language).
  Use the episode id from the [E03] header and the scene id from the nearest preceding [E03-S02] marker.
  If you are unsure of a quote, choose another one instead of reconstructing it.
- Report genuine ambiguity: set confidence honestly, fill ambiguity_note, list alternative_classifications.
- Write all analysis in English. Do not invent scenes, characters or dialogue."""


def build_user_prompt(marked: str, episode_count: int) -> str:
    return (f"The screenplay has {episode_count} detected episodes. Episode headers look like "
            f"'=== [E03] EPISODE 3 Title ===' and scene markers look like '[E03-S02]'.\n\n"
            f"SCREENPLAY:\n{marked}")
