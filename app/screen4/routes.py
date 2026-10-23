from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db, Decision, ConceptVersion
from app.screen2.models import Screenplay
from app.screen4.schemas import Screen4GatesResponse
from app.screen4.service import Screen4Service
from app.service import list_concepts

router = APIRouter(prefix="/api/screen4", tags=["Screen 4 - Gates & Intensity Meters"])


def get_screen4_service():
    return Screen4Service()  # provider initialisation is lazy and cache-aware


def _latest_decision(db: Session, project_id: int):
    return db.scalar(select(Decision).join(ConceptVersion, Decision.version_id == ConceptVersion.id)
        .where(ConceptVersion.concept_id == project_id).order_by(Decision.id.desc()))


@router.get("/projects")
def screen4_projects(db: Session = Depends(get_db)):
    projects = []
    for concept in list_concepts(db):
        decision = _latest_decision(db, concept["id"])
        screenplay = db.scalar(select(Screenplay).where(Screenplay.concept_id == concept["id"])
            .order_by(Screenplay.version_no.desc()).limit(1))
        status = decision.decision if decision else "pending"
        projects.append({"id": concept["id"], "title": concept["title"],
            "approval_status": status,
            "approved": status in ("approve_to_screenplay", "approved", "approve"),
            "screenplay_version": screenplay.version_no if screenplay else None,
            "screenplay_title": screenplay.title if screenplay else None,
            "parse_status": screenplay.parse_status if screenplay else None,
            "word_count": (screenplay.parse or {}).get("word_count", 0) if screenplay else 0})
    return projects


@router.get("/analyze/{project_id}", response_model=Screen4GatesResponse)
async def get_screenplay_gates_and_meters(project_id: int, db: Session = Depends(get_db),
        service: Screen4Service = Depends(get_screen4_service),
        x_user_name: str | None = Header(default="Writer")):
    try:
        decision = _latest_decision(db, project_id)
        status = decision.decision if decision else "pending"
        if status not in ("approve_to_screenplay", "approved", "approve"):
            raise HTTPException(status_code=400, detail="Concept approval is required before Screen 4 analysis.")
        return await service.analyze_gates_and_meters(db, project_id,
            user_name=(x_user_name or "Writer").strip() or "Writer")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Screen 4 analysis failed: {str(exc)}")
