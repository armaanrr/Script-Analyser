"""Screen 10: append-only human decisions, checklist snapshots, overrides and learning links."""
from datetime import datetime
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base, now


class Screen10Decision(Base):
    __tablename__ = "screen10_decisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), index=True)
    screenplay_id: Mapped[int | None] = mapped_column(ForeignKey("screenplays.id"), nullable=True, index=True)
    decision_type: Mapped[str] = mapped_column(String(30))  # concept | screenplay
    decision: Mapped[str] = mapped_column(String(40))
    rationale: Mapped[str] = mapped_column(Text)
    reviewer_name: Mapped[str] = mapped_column(String(120))
    reviewer_role: Mapped[str] = mapped_column(String(30))
    version_label: Mapped[str] = mapped_column(String(120), default="")
    analysis_run_id: Mapped[str] = mapped_column(String(500), default="")
    analysis_provenance: Mapped[str] = mapped_column(Text, default="")
    ai_score_at_decision: Mapped[str] = mapped_column(String(40), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Screen10ChecklistSnapshot(Base):
    __tablename__ = "screen10_checklist_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), index=True)
    screenplay_id: Mapped[int] = mapped_column(ForeignKey("screenplays.id"), index=True)
    items: Mapped[dict] = mapped_column(JSON, default=dict)
    reviewer_name: Mapped[str] = mapped_column(String(120))
    reviewer_role: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Screen10Override(Base):
    __tablename__ = "screen10_overrides"
    id: Mapped[int] = mapped_column(primary_key=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), index=True)
    screenplay_id: Mapped[int] = mapped_column(ForeignKey("screenplays.id"), index=True)
    field_key: Mapped[str] = mapped_column(String(100))
    original_value: Mapped[str] = mapped_column(Text)
    adjusted_value: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text)
    reviewer_name: Mapped[str] = mapped_column(String(120))
    reviewer_role: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Screen10LearningLink(Base):
    __tablename__ = "screen10_learning_links"
    id: Mapped[int] = mapped_column(primary_key=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), index=True)
    screenplay_id: Mapped[int] = mapped_column(ForeignKey("screenplays.id"), index=True)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    source_name: Mapped[str] = mapped_column(String(200), default="")
    reporting_window: Mapped[str] = mapped_column(String(200), default="")
    extracted_at: Mapped[str] = mapped_column(String(80), default="")
    note: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
