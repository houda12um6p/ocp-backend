"""
Scoring engine for merge requests and developers.

Formula (optimized):
    Score = 1000 × e^(-0.07 × max(0, Xnorm - Δ))

"""

import math

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models.merge_request import MergeRequest
from ..models.review_comment import ReviewComment
from ..models.user import User

# Harshness constant: every 10 excess normalized severity points halves the score
k: float = 0.07


def calculate_mr_score(mr_id: str, db: Session) -> float:
    """
    Calculate and save the score for one MergeRequest.

    Steps:
      1. Load the MR (404 if missing)
      2. X     sum of severity_weight across all review comments
      3. L     total lines modified in this MR
      4. Xnorm normalize X by PR size so large PRs aren't penalized unfairly
      5. delta  story-point allowance from the linked Jira task
      6. Apply the formula and round to 2 decimal places
      7. Persist the new score and return it
    """
    mr = db.query(MergeRequest).filter(MergeRequest.id == mr_id).first()
    if not mr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MergeRequest {mr_id} not found",
        )

    # X raw severity load (suggestions=0 contribute nothing)
    comments = (
        db.query(ReviewComment)
        .filter(ReviewComment.merge_request_id == mr_id)
        .all()
    )
    X = sum(c.severity_weight for c in comments)

    # L total lines changed in this PR (additions + deletions)
    L = mr.lines_modified or 0

    # Xnorm size-normalized severity: larger PRs naturally have more comments,
    # so we divide by sqrt(1 + L) to keep the scale fair
    Xnorm = X / math.sqrt(1 + L)

    # delta complexity allowance from the linked Jira task;
    # more story points = harder task = more free severity before penalty kicks in
    delta = mr.jira_task.story_points if mr.jira_task else 0

    # Apply the formula: penalty only starts once Xnorm exceeds the allowance
    x = max(0.0, Xnorm - delta)
    score = round(1000 * math.exp(-k * x), 2)

    # Persist the result
    mr.score = score
    db.commit()

    return score


def calculate_developer_score(user_id: str, db: Session) -> float:
    """
    Sum all MR scores for a developer and save to User.total_score.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    # Sum scores across all MRs authored by this developer
    mrs = (
        db.query(MergeRequest)
        .filter(MergeRequest.author_id == user_id)
        .all()
    )
    total = sum(mr.score or 0.0 for mr in mrs)

    # Persist the total
    user.total_score = total
    db.commit()

    return total


def calculate_project_score(project_id: str, db: Session) -> float:
    """
    Recalculate every MR score in a project, then every developer total.
    Returns the sum of all MR scores (project-level total).
    """
    mrs = (
        db.query(MergeRequest)
        .filter(MergeRequest.project_id == project_id)
        .all()
    )

    # Recalculate each MR and collect fresh scores
    mr_scores = [calculate_mr_score(mr.id, db) for mr in mrs]

    # Recalculate each unique developer who has an MR in this project
    author_ids = {mr.author_id for mr in mrs if mr.author_id}
    for user_id in author_ids:
        calculate_developer_score(user_id, db)

    return sum(mr_scores)
