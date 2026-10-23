from datetime import datetime
from typing import Optional
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ..db import Base, now


class Screenplay(Base):
    """One uploaded screenplay version for an approved concept. Raw text is stored normalised,
    so character offsets in `parse` always point at exactly this text."""
    __tablename__ = "screenplays"
    __table_args__ = (UniqueConstraint("concept_id", "version_no"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(10))            # upload | paste
    text_sha256: Mapped[str] = mapped_column(String(64))
    raw_text: Mapped[str] = mapped_column(Text)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expected_episodes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parse: Mapped[dict] = mapped_column(JSON)
    parse_status: Mapped[str] = mapped_column(String(10))           # ok | partial | failed
    declared: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)   # script-declared genre labels
    uploaded_by: Mapped[str] = mapped_column(String(120))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ModuleRun(Base):
    """One run of one analysis module (classification now; scorecard, gates... in later screens)."""
    __tablename__ = "screenplay_module_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    screenplay_id: Mapped[int] = mapped_column(ForeignKey("screenplays.id"), index=True)
    module: Mapped[str] = mapped_column(String(30), index=True)
    cache_key: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(80))
    prompt_version: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(10))                 # ok | failed
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ClassificationReview(Base):
    """Append-only. AI and script-declared values are never overwritten; the user-confirmed
    value is simply the latest confirm/edit row."""
    __tablename__ = "classification_reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    screenplay_id: Mapped[int] = mapped_column(ForeignKey("screenplays.id"), index=True)
    module_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("screenplay_module_runs.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(10))                 # confirm | edit | flag
    primary_genre: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    secondary_genre: Mapped[Optional[str]] = mapped_column(String(240), nullable=True)
    subgenre: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewer_name: Mapped[str] = mapped_column(String(120))
    reviewer_role: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
