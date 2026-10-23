import io
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.config import settings
from app.screen2.service import run_screen2_analysis, Screen2ServiceError

router = APIRouter(prefix="/api/screen2", tags=["Screen 2 - Overview & Genre"])


def get_current_user(
    x_user_name: str | None = Header(default="Armaan"),
    x_user_role: str | None = Header(default="producer")
):
    name = (x_user_name or "Armaan").strip()
    role = (x_user_role or "producer").strip()
    if role not in settings.roles or not name:
        raise HTTPException(status_code=401, detail="Unknown user or role.")
    return {"name": name, "role": role}


def extract_raw_text(file_bytes: bytes, filename: str) -> str:
    """Extracts raw text from .txt, .docx, or .pdf uploads."""
    ext = filename.lower().split(".")[-1]
    
    if ext == "txt":
        text = file_bytes.decode("utf-8", errors="ignore")
    elif ext == "docx":
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract text from DOCX file: {str(e)}")
    elif ext == "pdf":
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text = "\n".join([page.extract_text() or "" for page in reader.pages])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract text from PDF file: {str(e)}")
    else:
        text = file_bytes.decode("utf-8", errors="ignore")
        
    if not text.strip():
        raise HTTPException(status_code=400, detail=f"File '{filename}' contains no extractable text.")
        
    return text


@router.post("/analyze")
async def analyze_screenplay(
    concept_id: int = Form(...),
    title: str = Form(...),
    expected_episodes: int | None = Form(default=None),
    scene_marking: str = Form(default="unmarked"),
    scene_allocation: str = Form(default="fixed"),
    target_scenes_per_episode: int = Form(default=3),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Processes screenplay upload, parses structure, runs Gemini classification, and records execution."""
    try:
        content = await file.read()
        raw_text = extract_raw_text(content, file.filename)
        
        # Execute Screen 2 Pipeline (Parse + Gemini AI Classification)
        result = await run_screen2_analysis(
            db=db,
            concept_id=concept_id,
            title=title,
            filename=file.filename,
            raw_text=raw_text,
            expected_episodes=expected_episodes,
            scene_marking=scene_marking,
            scene_allocation=scene_allocation,
            target_scenes_per_episode=target_scenes_per_episode,
            user_name=user["name"]
        )
        return result

    except Screen2ServiceError as e:
        raise HTTPException(status_code=e.status, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screenplay Processing Error: {str(e)}")