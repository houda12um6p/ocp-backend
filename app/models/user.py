from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Enum
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum
import uuid


class UserRole(str, enum.Enum):
    DEVELOPER = "developer"
    MANAGER = "manager"


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.DEVELOPER)
    total_score = Column(Float, default=0.0)
    # Added default so records can be created without passing a timestamp explicitly
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    # passive_deletes   =True: let the DB handle SET NULL via ondelete on the FK side,
    # instead of SQLAlchemy nullifying children in Python before deleting the User
    merge_requests = relationship("MergeRequest", back_populates="author", passive_deletes=True)
    commits = relationship("Commit", back_populates="author", passive_deletes=True)
    review_comments = relationship("ReviewComment", back_populates="author", passive_deletes=True)
