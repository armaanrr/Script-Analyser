from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db, Decision, ConceptVersion
from app.screen8.schemas import (
    Screen8PromoResponse, CastingDecisionRequest, CastingDecisionResponse
)
from app.screen8.service import Screen8Service
from app.llm import get_provider

router = APIRouter(prefix="/api/screen8", tags=["Screen 8 - Promo, Season & Casting"])


def get_screen8_service():
    return Screen8Service(llm_provider=get_provider())


@router.get("/analyze/{project_id}", response_model=Screen8PromoResponse)
async def get_promo_and_casting_analysis(
    project_id: int,
    db: Session = Depends(get_db),
    service: Screen8Service = Depends(get_screen8_service)
):
    try:
        # Check concept approval status
        last_decision = db.scalar(
            select(Decision)
            .join(ConceptVersion, Decision.version_id == ConceptVersion.id)
            .where(ConceptVersion.concept_id == project_id)
            .order_by(Decision.id.desc())
        )

        status = last_decision.decision if last_decision else "pending"
        if status not in ("approve_to_screenplay", "approved", "approve"):
            raise HTTPException(status_code=400, detail="Approval Pending")

        return await service.analyze_promo_and_casting(db, project_id)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screen 08 Analysis Failed: {str(e)}")


@router.post("/decision/{project_id}", response_model=CastingDecisionResponse)
async def record_human_casting_decision(
    project_id: int,
    req: CastingDecisionRequest,
    db: Session = Depends(get_db),
    service: Screen8Service = Depends(get_screen8_service)
):
    try:
        if len(req.rationale.strip()) < 10:
            raise HTTPException(status_code=422, detail="Please provide a rationale of at least 10 characters.")
        await service.save_casting_decision(
            db=db,
            project_id=project_id,
            candidate_name=req.candidate_name,
            target_role=req.target_role,
            decision=req.decision,
            rationale=req.rationale,
            decided_by=req.decided_by
        )
        return CastingDecisionResponse(
            status="ok",
            message="Casting decision saved to audit log successfully",
            candidate_name=req.candidate_name,
            decision=req.decision,
            rationale=req.rationale,
            decided_by=req.decided_by
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record decision: {str(e)}")