from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from ..core.database import Base
import uuid


class JiraTask(Base):
    __tablename__ = "jira_tasks"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    jira_key = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    # Kept as String  -> Jira statuses are project-specific and can't be enumerated statically
    status = Column(String, nullable=False)
    story_points = Column(Integer, default=0)
    # Added defaults so records can be created without passing timestamps explicitly
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    merge_requests = relationship("MergeRequest", back_populates="jira_task")
