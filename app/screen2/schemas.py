from typing import Literal, Optional
from pydantic import BaseModel


class ReviewIn(BaseModel):
    action: Literal["confirm", "edit", "flag"]
    primary_genre: Optional[str] = None
    secondary_genre: Optional[str] = None
    subgenre: Optional[str] = None
    note: Optional[str] = None
