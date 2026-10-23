from dataclasses import dataclass
from typing import Optional, Protocol, Type
from pydantic import BaseModel


@dataclass
class LLMResult:
    parsed: BaseModel
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


class LLMProvider(Protocol):
    name: str
    model: str

    def generate_json(self, system: str, user: str, schema: Type[BaseModel]) -> LLMResult: ...
