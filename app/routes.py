from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from . import service
from .config import settings
from .db import get_db
from .schemas import ConceptInput, DecisionIn

router = APIRouter(prefix="/api")


class User(BaseModel):
    name: str
    role: str


def current_user(
    x_user_name: str | None = Header(default="Writer"),  # 👈 Added default fallback
    x_user_role: str | None = Header(default="writer")   # 👈 Added default fallback
) -> User:
    """Authentication header parser with default fallbacks for frontend integration."""
    name = (x_user_name or "Writer").strip()
    role = (x_user_role or "writer").strip()
    
    if role not in settings.roles or not name:
        raise HTTPException(401, "Unknown user or role.")
    return User(name=name, role=role)


def _wrap(fn, *a):
    try:
        return fn(*a)
    except service.ServiceError as e:
        raise HTTPException(e.status, e.message)


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {
        "name": user.name, 
        "role": user.role,
        "can_submit": user.role in settings.submit_roles,
        "can_decide": user.role in settings.decision_roles
    }


@router.get("/concepts")
def concepts(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return service.list_concepts(db)


@router.post("/concepts", status_code=201)
def create(c: ConceptInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.role not in settings.submit_roles:
        raise HTTPException(403, "Your role cannot submit concepts.")
    concept = _wrap(service.create_concept, db, user, c)
    return service.concept_detail(db, concept.id)


@router.put("/concepts/{cid}")
def new_version(cid: int, c: ConceptInput, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.role not in settings.submit_roles:
        raise HTTPException(403, "Your role cannot edit concepts.")
    _wrap(service.add_version, db, user, cid, c)
    return service.concept_detail(db, cid)


@router.get("/concepts/{cid}")
def detail(cid: int, version: int | None = None, db: Session = Depends(get_db),
           user: User = Depends(current_user)):
    return _wrap(service.concept_detail, db, cid, version)


@router.post("/concepts/{cid}/analyze")
def analyze(cid: int, version: int | None = None, force: bool = False,
            db: Session = Depends(get_db), user: User = Depends(current_user)):
    _wrap(service.run_analysis, db, user, cid, version, force)
    return service.concept_detail(db, cid, version)


@router.post("/concepts/{cid}/decision", status_code=201)
def decide(cid: int, d: DecisionIn, version: int | None = None,
           db: Session = Depends(get_db), user: User = Depends(current_user)):
    _wrap(service.record_decision, db, user, cid, version, d)
    return service.concept_detail(db, cid, version)