"""Deterministic checks that run BEFORE any LLM call."""
import re
from .config import settings
from .schemas import ConceptInput

SLUGLINE = re.compile(r"^\s*(INT\.|EXT\.|INT/EXT\.|I/E\.)", re.I | re.M)


def concept_only_problems(c: ConceptInput) -> list[str]:
    text = " ".join([c.logline, c.synopsis, c.dramatic_mechanism, c.characters_setup, c.likely_twists])
    problems = []
    words = len(text.split())
    if words > settings.max_concept_words:
        problems.append(f"Concept is {words} words; Stage 1 accepts up to {settings.max_concept_words}. "
                        "Submit the premise and synopsis, not the screenplay.")
    if len(SLUGLINE.findall(text)) >= 3:
        problems.append("Text looks like screenplay scenes (INT./EXT. sluglines). Stage 1 is concept-only; "
                        "full scripts are analysed in Stage 2.")
    return problems
