"""Gemini provider using the current google-genai SDK and the shared JSON interface."""
from typing import Type
from google import genai
from google.genai import types
from pydantic import BaseModel
from app.config import settings
from .base import LLMResult


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model or "gemini-2.5-flash"
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in the project .env file.")
        self.client = genai.Client(api_key=self.api_key)

    def generate_json(self, system: str, user: str, schema: Type[BaseModel]) -> LLMResult:
        """Make one structured-output call; return parsed data and usage for cost tracking."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.2,
            ),
        )
        if not getattr(response, "text", None):
            raise ValueError("Gemini returned an empty response.")
        parsed = schema.model_validate_json(response.text)
        usage = getattr(response, "usage_metadata", None)
        return LLMResult(
            parsed=parsed,
            input_tokens=getattr(usage, "prompt_token_count", None),
            output_tokens=getattr(usage, "candidates_token_count", None),
        )
