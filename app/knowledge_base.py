"""Knowledge-base seam. Today: nothing connected. Later: Rocket Reels shows, authorised
reference titles and verified analytics metrics plug in here without touching Screen 1 code."""
from typing import Protocol
from pydantic import BaseModel
from .schemas import ConceptInput, TractionRecord


class ReferenceTitle(BaseModel):
    title: str
    summary: str
    source: str = "knowledge_base"


class KnowledgeBase(Protocol):
    def reference_titles(self, concept: ConceptInput) -> list[ReferenceTitle]: ...
    def traction_for(self, titles: list[str]) -> list[TractionRecord]: ...


class NullKnowledgeBase:
    def reference_titles(self, concept: ConceptInput) -> list[ReferenceTitle]:
        return []

    def traction_for(self, titles: list[str]) -> list[TractionRecord]:
        return [TractionRecord(title=t, available=False,
                               reason="Knowledge base / verified analytics not connected yet.")
                for t in titles]


def get_kb() -> KnowledgeBase:
    return NullKnowledgeBase()
