import json
from .knowledge_base import ReferenceTitle
from .schemas import ConceptInput

SYSTEM = """You are a development analyst for Rocket Reels, a vertical-drama OTT platform
(~30 short episodes per show). You assess a CONCEPT (not a screenplay) so human creative leadership
can decide whether it deserves a full screenplay. You advise; humans decide.

Rules:
- Use only the submitted concept and the reference titles supplied. Never invent metrics, view counts,
  ratings, platform data or quotes. Traction numbers are NOT your job; leave them out.
- If no reference titles are supplied, you may name well-known public titles from general knowledge, but
  mark them source="model_general_knowledge" and keep claims modest.
- Similarity is a review signal, not proof of copying. Always state specific differences too.
- Audience and appeal-barrier statements are hypotheses with a confidence level, not facts.
  Never treat women 24-45 (or any group) as one homogeneous audience.
- Development ideas (2-4) must be specific, actionable and say how to keep the concept original.
- Rate each of the six dimensions 0-10. If evidence is genuinely insufficient, set rating to null and say why.
  Do not compute points or totals. Do not give an approve/reject recommendation.
- Rate "comparables" on the quality of the comparison only; you have no verified traction data.
- Be concise and concrete. Cite which part of the submission supports each rating."""

RUBRIC = """Dimensions (dimension_key: what it tests):
- originality: premise freshness, distinct dramatic mechanism, execution opportunity
- comparables: quality of comparable-title selection and comparison
- taxonomy: clarity of primary/secondary category, genre and subgenre
- women_24_45_development: actionable, audience-specific development without losing originality
- audience_id: evidence-based primary and secondary audience hypotheses
- micro_drama_engine: can the premise sustain progressive hooks, reversals and payoffs across ~30 short episodes"""


def build_user_prompt(c: ConceptInput, refs: list[ReferenceTitle]) -> str:
    refs_block = (
        json.dumps(
            [r.model_dump() for r in refs],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        if refs
        else "NONE SUPPLIED (knowledge base not connected)."
    )

    concept_json = json.dumps(
        c.model_dump(),
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return (
        f"{RUBRIC}\n\n"
        f"AUTHORIZED REFERENCE TITLES:\n{refs_block}\n\n"
        f"CONCEPT SUBMISSION:\n{concept_json}"
    )