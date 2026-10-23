from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.db import Base, engine


class Screen9RewriteTask(Base):
    __tablename__ = "screen9_rewrite_tasks"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, nullable=False, index=True)
    screenplay_version = Column(Integer, nullable=False, default=1)
    task_key = Column(String(50), nullable=False)
    priority = Column(String(20), nullable=False)  # High, Medium, Low
    target_scenes = Column(String(100), nullable=False)
    issue_identified = Column(Text, nullable=False)
    proposed_rewrite = Column(Text, nullable=False)
    expected_impact = Column(Text, nullable=False)
    owner = Column(String(100), default="Writer")
    status = Column(String(50), default="Open")  # Open, In Progress, Resolved
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Initialize table in SQLite
Base.metadata.create_all(bind=engine)