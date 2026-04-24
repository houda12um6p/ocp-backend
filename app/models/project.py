from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum
import uuid


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Project(Base):
    __tablename__ = "projects"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    repo_url = Column(String, nullable=False)
    # Fixed now uses ProjectStatus enum instead of plain String
    status = Column(Enum(ProjectStatus), nullable=False)
    # Added default so records can be created without passing a timestamp explicitly
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    # deleting a Project removes its MergeRequests and Alerts
    merge_requests = relationship("MergeRequest", back_populates="project", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="project", cascade="all, delete-orphan")
