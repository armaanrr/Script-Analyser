from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db, Decision, ConceptVersion
from app.screen2.models import Screenplay
from app.screen3.schemas import ScorecardResponse
from app.screen3.service import Screen3Service
from app.service import list_concepts

router = APIRouter(prefix="/api/screen3", tags=["Screen 3 - Scorecard"])


class ScorecardRequest(BaseModel):
    script_text: str | None = None


def get_screen3_service():
    # Provider creation is lazy; cached results do not initialise an API client.
    return Screen3Service()


def _latest_decision(db: Session, concept_id: int):
    return db.scalar(select(Decision)
        .join(ConceptVersion, Decision.version_id == ConceptVersion.id)
        .where(ConceptVersion.concept_id == concept_id)
        .order_by(Decision.id.desc()))


@router.get("/projects")
def scorecard_projects(db: Session = Depends(get_db)):
    """Concepts with their latest screenplay and approval status for the Screen 3 picker."""
    result = []
    for concept in list_concepts(db):
        screenplay = db.scalar(select(Screenplay)
            .where(Screenplay.concept_id == concept["id"])
            .order_by(Screenplay.version_no.desc()).limit(1))
        decision = _latest_decision(db, concept["id"])
        approved = bool(decision and decision.decision in ("approve_to_screenplay", "approved", "approve"))
        result.append({
            "id": concept["id"], "title": concept["title"],
            "approval_status": decision.decision if decision else "pending",
            "approved": approved,
            "screenplay_id": screenplay.id if screenplay else None,
            "screenplay_title": screenplay.title if screenplay else None,
            "screenplay_version": screenplay.version_no if screenplay else None,
            "parse_status": screenplay.parse_status if screenplay else None,
            "word_count": (screenplay.parse or {}).get("word_count", 0) if screenplay else 0,
            "scene_count": (screenplay.parse or {}).get("scene_count", 0) if screenplay else 0,
            "episode_count": (screenplay.parse or {}).get("detected_count", 0) if screenplay else 0,
        })
    return result


@router.post("/analyze/{project_id}", response_model=ScorecardResponse)
async def analyze_screenplay_scorecard(
    project_id: int,
    req: ScorecardRequest | None = None,
    db: Session = Depends(get_db),
    service: Screen3Service = Depends(get_screen3_service),
    x_user_name: str | None = Header(default="Writer"),
):
    decision = _latest_decision(db, project_id)
    status = decision.decision if decision else "pending"
    if status not in ("approve_to_screenplay", "approved", "approve"):
        raise HTTPException(status_code=400, detail="Concept approval is required before Screen 3 analysis.")

    screenplay = db.scalar(select(Screenplay)
        .where(Screenplay.concept_id == project_id)
        .order_by(Screenplay.version_no.desc()).limit(1))
    script_text = (req.script_text.strip() if req and req.script_text else None) or (screenplay.raw_text if screenplay else None)
    if not script_text:
        raise HTTPException(status_code=400, detail="No screenplay found. Upload and process a screenplay on Screen 2 first.")
    try:
        return await service.analyze_scorecard(project_id, script_text, db=db,
            screenplay=screenplay, user_name=(x_user_name or "Writer").strip() or "Writer")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Keep a clear actionable message while logging detail in the server console.
        raise HTTPException(status_code=500, detail=f"Scorecard analysis failed: {str(e)}")
