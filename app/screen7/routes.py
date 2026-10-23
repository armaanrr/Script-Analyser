from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db, Decision, ConceptVersion
from app.screen2.models import Screenplay
from app.screen7.schemas import Screen7AudienceResponse
from app.screen7.service import Screen7Service
from app.service import list_concepts

router = APIRouter(prefix="/api/screen7", tags=["Screen 7 - Audience, Title & World"])
APPROVED = ("approve_to_screenplay", "approved", "approve")


def get_screen7_service():
    return Screen7Service()


def _latest_decision(db: Session, project_id: int):
    return db.scalar(select(Decision).join(ConceptVersion, Decision.version_id == ConceptVersion.id)
        .where(ConceptVersion.concept_id == project_id).order_by(Decision.id.desc()))


@router.get("/projects")
def screen7_projects(db: Session = Depends(get_db)):
    projects = []
    for concept in list_concepts(db):
        decision = _latest_decision(db, concept["id"])
        screenplay = db.scalar(select(Screenplay).where(Screenplay.concept_id == concept["id"])
            .order_by(Screenplay.version_no.desc()).limit(1))
        status = decision.decision if decision else "pending"
        projects.append({"id": concept["id"], "title": concept.get("title") or concept.get("working_title") or f"Concept #{concept['id']}",
            "approval_status": status, "approved": status in APPROVED,
            "screenplay_version": screenplay.version_no if screenplay else None,
            "screenplay_title": screenplay.title if screenplay else None,
            "parse_status": screenplay.parse_status if screenplay else None,
            "word_count": (screenplay.parse or {}).get("word_count", 0) if screenplay else 0})
    return projects


@router.get("/analyze/{project_id}", response_model=Screen7AudienceResponse)
async def get_audience_and_world_analysis(project_id: int, db: Session = Depends(get_db),
        service: Screen7Service = Depends(get_screen7_service),
        x_user_name: str | None = Header(default="Writer")):
    try:
        decision = _latest_decision(db, project_id)
        status = decision.decision if decision else "pending"
        if status not in APPROVED:
            raise HTTPException(status_code=400, detail="Concept approval is required before Screen 7 analysis.")
        return await service.analyze_audience_and_world(db, project_id,
            user_name=(x_user_name or "Writer").strip() or "Writer")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Screen 7 audience/title/world analysis failed: {str(exc)}")
