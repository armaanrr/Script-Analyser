from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db, Decision, ConceptVersion
from app.screen2.models import Screenplay
from app.screen5.schemas import Screen5DiagnosticsResponse
from app.screen5.service import Screen5Service
from app.service import list_concepts

router = APIRouter(prefix="/api/screen5", tags=["Screen 5 - Episode Diagnostics"])


def get_screen5_service():
    return Screen5Service()  # provider creation is lazy; successful cache hits avoid API setup/cost.


def _latest_decision(db: Session, project_id: int):
    return db.scalar(select(Decision).join(ConceptVersion, Decision.version_id == ConceptVersion.id)
        .where(ConceptVersion.concept_id == project_id).order_by(Decision.id.desc()))


@router.get("/projects")
def screen5_projects(db: Session = Depends(get_db)):
    projects = []
    for concept in list_concepts(db):
        decision = _latest_decision(db, concept["id"])
        screenplay = db.scalar(select(Screenplay).where(Screenplay.concept_id == concept["id"])
            .order_by(Screenplay.version_no.desc()).limit(1))
        status = decision.decision if decision else "pending"
        projects.append({"id": concept["id"], "title": concept.get("title") or concept.get("working_title") or f"Concept #{concept['id']}",
            "approval_status": status,
            "approved": status in ("approve_to_screenplay", "approved", "approve"),
            "screenplay_version": screenplay.version_no if screenplay else None,
            "screenplay_title": screenplay.title if screenplay else None,
            "parse_status": screenplay.parse_status if screenplay else None,
            "word_count": (screenplay.parse or {}).get("word_count", 0) if screenplay else 0})
    return projects


@router.get("/analyze/{project_id}", response_model=Screen5DiagnosticsResponse)
async def get_episode_diagnostics(project_id: int, db: Session = Depends(get_db),
        service: Screen5Service = Depends(get_screen5_service),
        x_user_name: str | None = Header(default="Writer")):
    try:
        decision = _latest_decision(db, project_id)
        status = decision.decision if decision else "pending"
        if status not in ("approve_to_screenplay", "approved", "approve"):
            raise HTTPException(status_code=400, detail="Concept approval is required before Screen 5 analysis.")
        return await service.analyze_episodes(db, project_id,
            user_name=(x_user_name or "Writer").strip() or "Writer")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Screen 5 episode diagnostics failed: {str(exc)}")
