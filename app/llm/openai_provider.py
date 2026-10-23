"""Ready for the later switch to OpenAI (set LLM_PROVIDER=openai + OPENAI_MODEL). Untested until then."""
from typing import Type
from pydantic import BaseModel
from .base import LLMResult


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str):
        from openai import OpenAI
        if not api_key or not model:
            raise RuntimeError("OPENAI_API_KEY and OPENAI_MODEL must be set.")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_json(self, system: str, user: str, schema: Type[BaseModel]) -> LLMResult:
        resp = self.client.responses.parse(
            model=self.model,
            input=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            text_format=schema,
        )
        if resp.output_parsed is None:
            raise ValueError("OpenAI returned no parsed output")
        usage = getattr(resp, "usage", None)
        return LLMResult(resp.output_parsed,
                         getattr(usage, "input_tokens", None),
                         getattr(usage, "output_tokens", None))
