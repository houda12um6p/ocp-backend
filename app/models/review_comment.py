from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..core.database import Base
import uuid


class ReviewComment(Base):
    __tablename__ = "review_comments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    body = Column(String, nullable=False)
    # Severity weight assigned by the LLM classifier:
    #   0 = suggestion (no penalty)
    #   1 = minor issue
    #   3 = correctness bug
    #   5 = critical issue
    severity_weight = Column(Integer, default=0)
    # nullable=True + SET NULL so comments survive when their author is deleted
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # CASCADE so comments are removed when their MergeRequest is deleted
    merge_request_id = Column(UUID(as_uuid=True), ForeignKey("merge_requests.id", ondelete="CASCADE"), nullable=False)
    # Added default so records can be created without passing a timestamp explicitly
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    author = relationship("User", back_populates="review_comments")
    merge_request = relationship("MergeRequest", back_populates="review_comments")

    def detect_problem(self) -> bool:
        problem_keywords = [
            'bug', 'error', 'issue', 'problem', 'fix', 'broken',
            'wrong', 'incorrect', 'fail', 'crash', 'exception'
        ]
        body_lower = self.body.lower()
        return any(keyword in body_lower for keyword in problem_keywords)
