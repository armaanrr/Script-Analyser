from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db, Decision, ConceptVersion, Concept
from app.screen9.schemas import Screen9ProductionResponse, UpdateTaskStatusRequest
from app.screen9.service import Screen9Service
from app.llm import get_provider

router = APIRouter(prefix="/api/screen9", tags=["Screen 9 - Production & Rewrite"])


def get_screen9_service():
    return Screen9Service(llm_provider=get_provider())


@router.get("/analyze/{project_id}", response_model=Screen9ProductionResponse)
async def get_production_breakdown(
    project_id: int,
    db: Session = Depends(get_db),
    service: Screen9Service = Depends(get_screen9_service)
):
    try:
        # 1. Fetch Concept record
        concept = db.scalar(select(Concept).where(Concept.id == project_id))
        if not concept:
            raise HTTPException(status_code=404, detail=f"Concept #{project_id} not found.")

        # 2. Check Decision Status (direct concept_id, version join, or relationship)
        decision_status = None

        if hasattr(Decision, "concept_id"):
            dec = db.scalar(
                select(Decision)
                .where(Decision.concept_id == project_id)
                .order_by(Decision.id.desc())
            )
            if dec:
                decision_status = dec.decision

        if not decision_status and hasattr(Decision, "version_id"):
            dec = db.scalar(
                select(Decision)
                .join(ConceptVersion, Decision.version_id == ConceptVersion.id)
                .where(ConceptVersion.concept_id == project_id)
                .order_by(Decision.id.desc())
            )
            if dec:
                decision_status = dec.decision

        if not decision_status and hasattr(concept, "decisions") and concept.decisions:
            decision_status = concept.decisions[-1].decision

        # 3. Verify approval status
        if decision_status and decision_status not in ("approve_to_screenplay", "approved", "approve"):
            raise HTTPException(status_code=400, detail=f"Concept approval is pending (Status: {decision_status}).")

        return await service.analyze_production_and_rewrite(db, project_id)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screen 09 Analysis Failed: {str(e)}")


@router.patch("/task/{project_id}/{task_id}")
async def update_rewrite_task(
    project_id: int,
    task_id: str,
    req: UpdateTaskStatusRequest,
    db: Session = Depends(get_db),
    service: Screen9Service = Depends(get_screen9_service)
):
    try:
        updated = await service.update_task_status(
            db=db,
            project_id=project_id,
            task_id=task_id,
            status=req.status,
            owner=req.owner
        )
        return {
            "status": "ok",
            "task_id": updated.task_key,
            "new_status": updated.status,
            "owner": updated.owner
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")