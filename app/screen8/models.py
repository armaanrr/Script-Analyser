from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.db import Base, engine


class CastingDecision(Base):
    __tablename__ = "casting_decisions"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, nullable=False, index=True)
    candidate_name = Column(String(120), nullable=False)
    target_role = Column(String(80), nullable=False)
    decision = Column(String(50), nullable=False)  # Shortlist, Research Further, Do Not Shortlist, Override
    rationale = Column(Text, nullable=False)
    decided_by = Column(String(100), default="Producer")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Ensure table is initialized
Base.metadata.create_all(bind=engine)