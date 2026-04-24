from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum
import re
import uuid
from typing import Optional


class MergeRequestStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class MergeRequest(Base):
    __tablename__ = "merge_requests"
    # Unique constraint so concurrent webhook deliveries for the same PR don't create duplicates
    __table_args__ = (UniqueConstraint("github_id", name="uq_merge_requests_github_id"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    github_id = Column(Integer, nullable=True)
    title = Column(String, nullable=False)
    # nullable=True + SET NULL so MergeRequests survive when their author is deleted
    author_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    jira_task_id = Column(String(36), ForeignKey("jira_tasks.id"), nullable=True)
    #  now uses MergeRequestStatus enum instead of plain String
    status = Column(Enum(MergeRequestStatus), nullable=False)
    score = Column(Float, default=0.0)
    story_points = Column(Integer, default=0)
    # Lines that were refactored in this MR — used as linear penalty Lr in scoring formula
    refactored_lines = Column(Integer, default=0)
    # Total lines changed (additions + deletions) represents L in the scoring formula
    lines_modified = Column(Integer, default=0)
    # Added defaults so records can be created without passing timestamps explicitly
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    author = relationship("User", back_populates="merge_requests")
    project = relationship("Project", back_populates="merge_requests")
    jira_task = relationship("JiraTask", back_populates="merge_requests")
    # deleting a MergeRequest removes its commits and review comments
    commits = relationship("Commit", back_populates="merge_request", cascade="all, delete-orphan")
    review_comments = relationship("ReviewComment", back_populates="merge_request", cascade="all, delete-orphan")

    def extract_jira_key(self) -> Optional[str]:
        pattern = r'([A-Z]+-\d+)'
        match = re.search(pattern, self.title)
        return match.group(1) if match else None
