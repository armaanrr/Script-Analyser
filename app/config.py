import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically load .env from the project root folder
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _csv(name: str, default: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in os.getenv(name, default).split(",") if x.strip())


class Settings:
    llm_provider = os.getenv("LLM_PROVIDER", "gemini")
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    openai_model = os.getenv("OPENAI_MODEL", "")
    database_url = os.getenv("DATABASE_URL", "sqlite:///./rocket_reels.db")

    prompt_version = "concept-v1"
    max_retries = int(os.getenv("LLM_MAX_ATTEMPTS", "1"))
    max_concept_words = 2500

    roles = ("owner", "producer", "director", "writer")
    submit_roles = _csv("SUBMIT_ROLES", "owner,producer,director,writer")
    decision_roles = _csv("DECISION_ROLES", "owner,producer")


settings = Settings()