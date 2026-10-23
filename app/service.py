import hashlib
import json
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import prompts
from . import db as models
from .config import settings
from .db import Analysis, Concept, ConceptVersion, Decision
from .guards import concept_only_problems
from .knowledge_base import get_kb
from .llm import get_provider
from .schemas import ConceptAnalysis, ConceptInput, DecisionIn
from .scoring import compute_score


class ServiceError(Exception):
    def __init__(self, status: int, message: str | list[str]):
        self.status, self.message = status, message


def _check_input(c: ConceptInput) -> None:
    problems = concept_only_problems(c)
    if problems:
        raise ServiceError(422, problems)


def get_version(db: Session, concept_id: int, version_no: int | None = None) -> ConceptVersion:
    q = select(ConceptVersion).where(ConceptVersion.concept_id == concept_id)
    q = q.where(ConceptVersion.version_no == version_no) if version_no else q.order_by(ConceptVersion.version_no.desc())
    v = db.scalars(q).first()
    if not v:
        raise ServiceError(404, "Concept or version not found.")
    return v


def list_concepts(db: Session) -> list[dict]:
    """Returns all submitted concepts with titles extracted from version JSON and latest decision status."""
    concepts = db.scalars(select(Concept).order_by(Concept.id.desc())).all()
    results = []
    for c in concepts:
        try:
            v = get_version(db, c.id)
            data = v.data if v and isinstance(v.data, dict) else {}
            title = data.get("working_title") or f"Concept #{c.id}"
            
            last_decision = db.scalars(
                select(Decision)
                .join(ConceptVersion, Decision.version_id == ConceptVersion.id)
                .where(ConceptVersion.concept_id == c.id)
                .order_by(Decision.id.desc())
            ).first()

            results.append({
                "id": c.id,
                "title": title,
                "version_no": v.version_no if v else 1,
                "created_by": c.created_by,
                "latest_decision": last_decision.decision if last_decision else "pending"
            })
        except ServiceError:
            continue
            
    return results


def create_concept(db: Session, user, c: ConceptInput) -> Concept:
    _check_input(c)
    concept = Concept(created_by=user.name)
    db.add(concept)
    db.flush()
    db.add(ConceptVersion(concept_id=concept.id, version_no=1, data=c.model_dump(), created_by=user.name))
    db.commit()
    return concept


def add_version(db: Session, user, concept_id: int, c: ConceptInput) -> ConceptVersion:
    _check_input(c)
    latest = get_version(db, concept_id)
    v = ConceptVersion(concept_id=concept_id, version_no=latest.version_no + 1,
                       data=c.model_dump(), created_by=user.name)
    db.add(v)
    db.commit()
    return v


def _cache_key(data: dict, provider) -> str:
    raw = json.dumps([data, provider.name, provider.model, settings.prompt_version], sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def latest_analysis(db: Session, version_id: int) -> Analysis | None:
    return db.scalars(select(Analysis).where(Analysis.version_id == version_id)
                      .order_by(Analysis.id.desc())).first()


def run_analysis(db: Session, user, concept_id: int, version_no: int | None, force: bool) -> Analysis:
    v = get_version(db, concept_id, version_no)
    concept = ConceptInput(**v.data)
    _check_input(concept)
    try:
        provider = get_provider()
    except Exception as e:
        raise ServiceError(503, f"LLM provider not available: {e}")

    key = _cache_key(v.data, provider)
    if not force:
        hit = db.scalars(select(Analysis).where(Analysis.version_id == v.id, Analysis.cache_key == key,
                                                Analysis.status == "ok").order_by(Analysis.id.desc())).first()
        if hit:
            return hit

    kb = get_kb()
    refs = kb.reference_titles(concept)
    user_prompt = prompts.build_user_prompt(concept, refs)

    result, last_err = None, None
    for _ in range(settings.max_retries):
        try:
            result = provider.generate_json(prompts.SYSTEM, user_prompt, ConceptAnalysis)
            break
        except Exception as e:
            last_err = str(e)[:500]

    row = Analysis(version_id=v.id, cache_key=key, provider=provider.name, model=provider.model,
                   prompt_version=settings.prompt_version, created_by=user.name, status="failed",
                   error=last_err)
    if result is not None:
        analysis: ConceptAnalysis = result.parsed
        titles = [t.title for t in analysis.comparable_titles]
        traction = kb.traction_for(titles)
        traction_verified = bool(traction) and all(t.available for t in traction)
        score = compute_score(analysis.ratings, traction_verified)
        row.status, row.error = "ok", None
        row.input_tokens, row.output_tokens = result.input_tokens, result.output_tokens
        row.result = {
            "analysis": analysis.model_dump(),
            "traction": [t.model_dump() for t in traction],
            "score": score.model_dump(),
            "references_supplied": len(refs),
        }
    db.add(row)
    db.commit()
    return row


def record_decision(db: Session, user, concept_id: int, version_no: int | None, d: DecisionIn) -> Decision:
    if user.role not in settings.decision_roles:
        raise ServiceError(403, f"Role '{user.role}' cannot record concept decisions.")
    v = get_version(db, concept_id, version_no)
    a = latest_analysis(db, v.id)
    ok = a if a and a.status == "ok" else None
    row = Decision(version_id=v.id, decision=d.decision, rationale=d.rationale.strip(),
                   reviewer_name=user.name, reviewer_role=user.role,
                   analysis_id=ok.id if ok else None,
                   ai_total_at_decision=(ok.result["score"]["total"] if ok else None))
    db.add(row)
    db.commit()
    return row


def concept_detail(db: Session, concept_id: int, version_no: int | None = None) -> dict:
    concept = db.get(Concept, concept_id)
    if not concept:
        raise ServiceError(404, "Concept not found.")
    versions = db.scalars(select(ConceptVersion).where(ConceptVersion.concept_id == concept_id)
                          .order_by(ConceptVersion.version_no)).all()
    cur = get_version(db, concept_id, version_no)
    a = latest_analysis(db, cur.id)
    by_version = {v.id: v.version_no for v in versions}
    decisions = db.scalars(select(Decision).where(Decision.version_id.in_(by_version))
                           .order_by(Decision.id.desc())).all()
    return {
        "id": concept.id, "created_by": concept.created_by, "created_at": concept.created_at,
        "versions": [{"version_no": v.version_no, "created_by": v.created_by, "created_at": v.created_at}
                     for v in versions],
        "current_version": {"version_no": cur.version_no, "data": cur.data, "created_at": cur.created_at},
        "analysis": None if a is None else {
            "id": a.id, "status": a.status, "error": a.error, "provider": a.provider, "model": a.model,
            "prompt_version": a.prompt_version, "created_at": a.created_at, "result": a.result},
        "decisions": [{"id": x.id, "version_no": by_version[x.version_id], "decision": x.decision,
                       "rationale": x.rationale, "reviewer_name": x.reviewer_name,
                       "reviewer_role": x.reviewer_role, "ai_total_at_decision": x.ai_total_at_decision,
                       "created_at": x.created_at} for x in decisions],
    }