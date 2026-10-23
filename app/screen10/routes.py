"""Human review and final decision APIs. No AI call is made by Screen 10."""
import json
from io import BytesIO
from xml.sax.saxutils import escape
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from app.db import get_db, Concept, ConceptVersion, Decision, Analysis
from app.screen2.models import Screenplay, ModuleRun
from app.screen8.models import CastingDecision
from app.screen10.models import Screen10Decision, Screen10ChecklistSnapshot, Screen10Override, Screen10LearningLink
from app.screen10.schemas import DecisionRequest, ChecklistRequest, OverrideRequest, LearningRequest
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether

router = APIRouter(prefix="/api/screen10", tags=["Screen 10 - Human Review & Audit"])
MODULES = [
    ("scorecard", "16-dimension scorecard"), ("gates_intensity", "Mandatory gates & intensity meters"),
    ("episode_diagnostics", "Episode diagnostics"), ("character_emotional_journey", "Character & emotional findings"),
    ("audience_title_world", "Audience, title & world-building"), ("promo_season_casting", "Promo assets & casting"),
    ("production_rewrite", "Production estimates & rewrite plan"),
]
CONCEPT_DECISIONS = {"approve_to_screenplay", "revise_concept", "hold_for_research", "reject_concept"}
SCREENPLAY_DECISIONS = {"approve_screenplay", "revise_screenplay", "hold_for_review", "reject_screenplay"}


def _latest_screenplay(db: Session, concept_id: int):
    return db.scalar(select(Screenplay).where(Screenplay.concept_id == concept_id).order_by(desc(Screenplay.version_no), desc(Screenplay.id)))


def _title(db: Session, concept_id: int) -> str:
    version = db.scalar(select(ConceptVersion).where(ConceptVersion.concept_id == concept_id).order_by(desc(ConceptVersion.version_no)))
    data = version.data if version and isinstance(version.data, dict) else {}
    return str(data.get("working_title") or data.get("title") or f"Concept #{concept_id}")


def _module_status(db: Session, screenplay_id: int):
    latest = {}
    runs = db.scalars(select(ModuleRun).where(ModuleRun.screenplay_id == screenplay_id).order_by(desc(ModuleRun.id))).all()
    for run in runs:
        if run.module not in latest:
            latest[run.module] = run
    result = []
    for key, label in MODULES:
        run = latest.get(key)
        result.append({"key": key, "label": label, "status": (run.status.title() if run else "Missing"),
                       "run_id": run.id if run else None, "provider": run.provider if run else None,
                       "model": run.model if run else None, "prompt_version": run.prompt_version if run else None,
                       "created_at": run.created_at.isoformat() if run and run.created_at else None,
                       "result": run.result if run and run.status == "ok" else None})
    return result


@router.get("/projects")
def projects(db: Session = Depends(get_db)):
    concepts = db.scalars(select(Concept).order_by(desc(Concept.id))).all()
    output = []
    for concept in concepts:
        screenplay = _latest_screenplay(db, concept.id)
        versions = db.scalars(select(ConceptVersion).where(ConceptVersion.concept_id == concept.id).order_by(desc(ConceptVersion.version_no))).all()
        latest_decision = db.scalar(select(Screen10Decision).where(Screen10Decision.concept_id == concept.id).order_by(desc(Screen10Decision.id)))
        legacy_decision = db.scalar(select(Decision).join(ConceptVersion, Decision.version_id == ConceptVersion.id)
                                    .where(ConceptVersion.concept_id == concept.id).order_by(desc(Decision.id)))
        latest_value = latest_decision.decision if latest_decision else (legacy_decision.decision if legacy_decision else None)
        latest_type = latest_decision.decision_type if latest_decision else ("concept" if legacy_decision else None)
        output.append({"concept_id": concept.id, "title": _title(db, concept.id), "concept_version": versions[0].version_no if versions else None,
                       "screenplay_id": screenplay.id if screenplay else None, "screenplay_version": screenplay.version_no if screenplay else None,
                       "screenplay_title": screenplay.title if screenplay else None, "parse_status": screenplay.parse_status if screenplay else "missing",
                       "latest_decision": latest_value, "latest_decision_type": latest_type})
    return output


@router.get("/dashboard/{concept_id}")
def dashboard(concept_id: int, db: Session = Depends(get_db)):
    concept = db.get(Concept, concept_id)
    if not concept:
        raise HTTPException(404, "Concept not found.")
    screenplay = _latest_screenplay(db, concept_id)
    concept_versions = db.scalars(select(ConceptVersion).where(ConceptVersion.concept_id == concept_id).order_by(desc(ConceptVersion.version_no))).all()
    decisions = db.scalars(select(Screen10Decision).where(Screen10Decision.concept_id == concept_id).order_by(desc(Screen10Decision.id))).all()
    decision_history = [{"id": d.id, "decision_type": d.decision_type, "decision": d.decision, "rationale": d.rationale,
        "reviewer_name": d.reviewer_name, "reviewer_role": d.reviewer_role, "version_label": d.version_label,
        "analysis_run_id": d.analysis_run_id, "analysis_provenance": d.analysis_provenance, "ai_score_at_decision": d.ai_score_at_decision,
        "created_at": d.created_at.isoformat() if d.created_at else None} for d in decisions]
    seen_decisions = {(d["decision"], d["reviewer_name"], d["rationale"]) for d in decision_history}
    legacy_decisions = db.scalars(select(Decision).join(ConceptVersion, Decision.version_id == ConceptVersion.id)
                                  .where(ConceptVersion.concept_id == concept_id).order_by(desc(Decision.id))).all()
    for d in legacy_decisions:
        signature = (d.decision, d.reviewer_name, d.rationale)
        if signature not in seen_decisions:
            version = db.get(ConceptVersion, d.version_id)
            decision_history.append({"id": f"concept-{d.id}", "decision_type": "concept", "decision": d.decision,
                "rationale": d.rationale, "reviewer_name": d.reviewer_name, "reviewer_role": d.reviewer_role,
                "version_label": f"Concept v{version.version_no}" if version else "Concept version unavailable",
                "analysis_run_id": str(d.analysis_id or ""), "analysis_provenance": "Legacy Screen 1 concept decision record",
                "ai_score_at_decision": str(d.ai_total_at_decision or ""), "created_at": d.created_at.isoformat() if d.created_at else None})
            seen_decisions.add(signature)
    decision_history.sort(key=lambda d: d.get("created_at") or "", reverse=True)
    overrides = db.scalars(select(Screen10Override).where(Screen10Override.concept_id == concept_id).order_by(desc(Screen10Override.id))).all()
    learning = db.scalars(select(Screen10LearningLink).where(Screen10LearningLink.concept_id == concept_id).order_by(desc(Screen10LearningLink.id))).all()
    cast = db.scalars(select(CastingDecision).where(CastingDecision.concept_id == concept_id).order_by(desc(CastingDecision.id))).all()
    if not screenplay:
        modules = []
        checklist = None
        screenplay_id = None
    else:
        modules = _module_status(db, screenplay.id)
        checklist = db.scalar(select(Screen10ChecklistSnapshot).where(Screen10ChecklistSnapshot.screenplay_id == screenplay.id).order_by(desc(Screen10ChecklistSnapshot.id)))
        screenplay_id = screenplay.id
    scorecard = next((m for m in modules if m["key"] == "scorecard"), None)
    gates = next((m for m in modules if m["key"] == "gates_intensity"), None)
    ratings = (scorecard or {}).get("result") or {}
    dimensions = ratings.get("dimensions") or ratings.get("scores") or []
    complete_ratings = len(dimensions) == 16 and all(isinstance(d, dict) and d.get("rating") is not None for d in dimensions)
    checklist_items = checklist.items if checklist else {}
    return {
        "concept": {"id": concept.id, "title": _title(db, concept_id), "version": concept_versions[0].version_no if concept_versions else None},
        "screenplay": None if not screenplay else {"id": screenplay.id, "title": screenplay.title, "version": screenplay.version_no,
            "uploaded_at": screenplay.uploaded_at.isoformat() if screenplay.uploaded_at else None, "page_count": screenplay.page_count,
            "expected_episodes": screenplay.expected_episodes, "parse_status": screenplay.parse_status,
            "detected_episodes": len((screenplay.parse or {}).get("episodes", [])) if isinstance(screenplay.parse, dict) else None,
            "text_sha256": screenplay.text_sha256},
        "modules": modules, "ratings_complete": complete_ratings,
        "gates_result": (gates or {}).get("result"), "checklist": checklist_items,
        "decisions": decision_history,
        "overrides": [{"id": o.id, "field_key": o.field_key, "original_value": o.original_value, "adjusted_value": o.adjusted_value,
            "rationale": o.rationale, "reviewer_name": o.reviewer_name, "reviewer_role": o.reviewer_role,
            "created_at": o.created_at.isoformat() if o.created_at else None} for o in overrides],
        "casting_decisions": [{"candidate_name": c.candidate_name, "target_role": c.target_role, "decision": c.decision,
            "rationale": c.rationale, "decided_by": c.decided_by, "created_at": c.created_at.isoformat() if c.created_at else None} for c in cast],
        "learning_links": [{"id": l.id, "source_name": l.source_name, "reporting_window": l.reporting_window,
            "extracted_at": l.extracted_at, "metrics": l.metrics, "note": l.note, "created_by": l.created_by,
            "created_at": l.created_at.isoformat() if l.created_at else None} for l in learning],
        "screenplay_id": screenplay_id,
        "completeness": "Missing" if not screenplay else ("Complete" if screenplay.parse_status == "ok" and all(m["status"] == "Ok" for m in modules) else "Partial")
    }


@router.post("/decision/{concept_id}", status_code=201)
def record_decision(concept_id: int, req: DecisionRequest, db: Session = Depends(get_db)):
    concept = db.get(Concept, concept_id)
    if not concept:
        raise HTTPException(404, "Concept not found.")
    screenplay = _latest_screenplay(db, concept_id)
    allowed = CONCEPT_DECISIONS if req.decision_type == "concept" else SCREENPLAY_DECISIONS
    if req.decision not in allowed:
        raise HTTPException(422, f"Invalid {req.decision_type} decision.")
    if req.reviewer_role not in {"owner", "producer"}:
        raise HTTPException(403, "Only an authorized owner or producer can record formal concept or screenplay decisions.")
    if req.decision_type == "screenplay":
        if not screenplay:
            raise HTTPException(400, "Upload a screenplay before recording a screenplay decision.")
        if req.decision == "approve_screenplay":
            dashboard_modules = _module_status(db, screenplay.id)
            missing = [m["label"] for m in dashboard_modules if m["status"] != "Ok"]
            if screenplay.parse_status != "ok" or missing:
                raise HTTPException(400, "Full screenplay approval is blocked until parsing is complete and all required modules are successful. Missing/incomplete: " + ", ".join(missing or ["screenplay parsing"]))
            score = next((m for m in dashboard_modules if m["key"] == "scorecard"), None)
            dims = ((score or {}).get("result") or {}).get("dimensions") or []
            if len(dims) != 16 or any(not isinstance(d, dict) or d.get("rating") is None or not d.get("evidence_excerpt") for d in dims):
                raise HTTPException(400, "Full screenplay approval is blocked until all 16 scorecard ratings include evidence. Review missing evidence on Screen 3.")
            latest_checklist = db.scalar(select(Screen10ChecklistSnapshot).where(Screen10ChecklistSnapshot.screenplay_id == screenplay.id).order_by(desc(Screen10ChecklistSnapshot.id)))
            required_checks = ["correct_version", "modules_complete", "scorecard_reviewed", "gates_resolved", "episodes_reviewed", "characters_reviewed", "promo_casting_reviewed", "production_reviewed"]
            checklist_items = latest_checklist.items if latest_checklist else {}
            unchecked = [key for key in required_checks if checklist_items.get(key) is not True]
            if unchecked:
                raise HTTPException(400, "Full screenplay approval is blocked. Save the checklist with every required item confirmed: " + ", ".join(unchecked))
    modules = _module_status(db, screenplay.id) if screenplay else []
    score = next((m for m in modules if m["key"] == "scorecard"), None)
    result = (score or {}).get("result") or {}
    ai_score = str(result.get("total_score", ""))
    run_ids = [str(m["run_id"]) for m in modules if m.get("run_id")]
    provenance = "; ".join(f"{m['label']}: provider={m.get('provider') or 'n/a'}, model={m.get('model') or 'n/a'}, prompt={m.get('prompt_version') or 'n/a'}, run={m.get('run_id') or 'n/a'}" for m in modules)
    row = Screen10Decision(concept_id=concept_id, screenplay_id=screenplay.id if screenplay else None,
        decision_type=req.decision_type, decision=req.decision, rationale=req.rationale.strip(), reviewer_name=req.reviewer_name.strip(),
        reviewer_role=req.reviewer_role, version_label=req.version_label or (f"v{screenplay.version_no}" if screenplay else f"concept-v{_title(db, concept_id)}"),
        analysis_run_id=",".join(run_ids), analysis_provenance=provenance, ai_score_at_decision=ai_score)
    db.add(row)
    # Keep Screen 1's established concept-decision workflow in sync with Screen 10.
    if req.decision_type == "concept":
        version = db.scalar(select(ConceptVersion).where(ConceptVersion.concept_id == concept_id).order_by(desc(ConceptVersion.version_no)))
        if version:
            analysis = db.scalar(select(Analysis).where(Analysis.version_id == version.id, Analysis.status == "ok").order_by(desc(Analysis.id)))
            db.add(Decision(version_id=version.id, decision=req.decision, reviewer_name=req.reviewer_name.strip(),
                reviewer_role=req.reviewer_role, rationale=req.rationale.strip(), analysis_id=analysis.id if analysis else None,
                ai_total_at_decision=None))
    db.commit(); db.refresh(row)
    return {"status": "saved", "decision_id": row.id, "created_at": row.created_at.isoformat() if row.created_at else None}


@router.post("/checklist/{concept_id}", status_code=201)
def save_checklist(concept_id: int, req: ChecklistRequest, db: Session = Depends(get_db)):
    screenplay = _latest_screenplay(db, concept_id)
    if not db.get(Concept, concept_id): raise HTTPException(404, "Concept not found.")
    if not screenplay: raise HTTPException(400, "Upload a screenplay before saving the review checklist.")
    row = Screen10ChecklistSnapshot(concept_id=concept_id, screenplay_id=screenplay.id, items=req.items,
                                    reviewer_name=req.reviewer_name.strip(), reviewer_role=req.reviewer_role)
    db.add(row); db.commit(); db.refresh(row)
    return {"status": "saved", "checklist_id": row.id}


@router.post("/override/{concept_id}", status_code=201)
def save_override(concept_id: int, req: OverrideRequest, db: Session = Depends(get_db)):
    screenplay = _latest_screenplay(db, concept_id)
    if not db.get(Concept, concept_id): raise HTTPException(404, "Concept not found.")
    if not screenplay: raise HTTPException(400, "Upload a screenplay before recording a screenplay override.")
    row = Screen10Override(concept_id=concept_id, screenplay_id=screenplay.id, field_key=req.field_key.strip(),
        original_value=req.original_value, adjusted_value=req.adjusted_value, rationale=req.rationale.strip(),
        reviewer_name=req.reviewer_name.strip(), reviewer_role=req.reviewer_role)
    db.add(row); db.commit(); db.refresh(row)
    return {"status": "saved", "override_id": row.id}


@router.post("/learning/{concept_id}", status_code=201)
def save_learning(concept_id: int, req: LearningRequest, db: Session = Depends(get_db)):
    screenplay = _latest_screenplay(db, concept_id)
    if not db.get(Concept, concept_id): raise HTTPException(404, "Concept not found.")
    if not screenplay: raise HTTPException(400, "Upload a screenplay before adding post-launch learning.")
    row = Screen10LearningLink(concept_id=concept_id, screenplay_id=screenplay.id, metrics=req.metrics, source_name=req.source_name.strip(),
        reporting_window=req.reporting_window.strip(), extracted_at=req.extracted_at.strip(), note=req.note,
        created_by=req.created_by.strip())
    db.add(row); db.commit(); db.refresh(row)
    return {"status": "saved", "learning_id": row.id}


@router.get("/export/{concept_id}.json")
def export_json(concept_id: int, db: Session = Depends(get_db)):
    data = dashboard(concept_id, db)
    payload = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    return Response(content=payload, media_type="application/json", headers={"Content-Disposition": f'attachment; filename="rocket_reels_concept_{concept_id}_review.json"'})


def _simple_pdf(lines: list[str]) -> bytes:
    """Create a paginated, printable PDF without truncating long audit histories."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=17*mm, leftMargin=17*mm,
                            topMargin=16*mm, bottomMargin=16*mm, title="Rocket Reels Human Review")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="RRHeading", parent=styles["Heading2"], textColor=colors.HexColor("#234f2b"), spaceBefore=8, spaceAfter=5))
    story = []
    for line in lines:
        if not line:
            story.append(Spacer(1, 4))
        elif line.isupper() and len(line) < 65:
            story.append(Paragraph(escape(line), styles["RRHeading"]))
        else:
            story.append(Paragraph(escape(line), styles["BodyText"]))
            story.append(Spacer(1, 3))
    doc.build(story)
    return buffer.getvalue()


@router.get("/export/{concept_id}.pdf")
def export_pdf(concept_id: int, db: Session = Depends(get_db)):
    data = dashboard(concept_id, db)
    lines = ["ROCKET REELS - HUMAN REVIEW & FINAL DECISION", f"Concept: {data['concept']['title']} (#{concept_id})",
        f"Concept version: {data['concept']['version']}", f"Screenplay: {(data['screenplay'] or {}).get('title', 'Not uploaded')}",
        f"Screenplay version: {(data['screenplay'] or {}).get('version', 'N/A')}", f"Completeness: {data['completeness']}", "",
        "MODULE STATUS:"]
    lines += [f"- {m['label']}: {m['status']}" for m in data["modules"]]
    lines += ["", "DECISION HISTORY:"]
    lines += [f"- {d['decision_type']}: {d['decision']} by {d['reviewer_name']} ({d['reviewer_role']}) on {d['created_at']}; rationale: {d['rationale']}" for d in data["decisions"]]
    lines += [f"  Provenance: {d.get('analysis_provenance', '')}" for d in data['decisions']]
    lines += ["", "OVERRIDES:"]
    lines += [f"- {o['field_key']}: {o['original_value']} -> {o['adjusted_value']}; rationale: {o['rationale']}" for o in data["overrides"]]
    return Response(content=_simple_pdf(lines), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="rocket_reels_concept_{concept_id}_review.pdf"'})
