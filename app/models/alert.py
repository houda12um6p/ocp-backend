from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum
import uuid


class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String, nullable=False)
    # Fixed:now uses AlertSeverity enum instead of plain String
    severity = Column(Enum(AlertSeverity), nullable=False)
    message = Column(String, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    is_resolved = Column(Boolean, default=False)
    # Added default so records can be created without passing a timestamp explicitly
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    project = relationship("Project", back_populates="alerts")
