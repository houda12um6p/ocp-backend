from datetime import timedelta
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.alert import Alert
from ..models.commit import Commit
from ..models.merge_request import MergeRequest, MergeRequestStatus
from ..models.project import Project
from ..models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/{project_id}/overview")
def get_overview(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    merge_requests = db.query(MergeRequest).filter(MergeRequest.project_id == project_id).all()
    open_count = sum(1 for mr in merge_requests if mr.status == MergeRequestStatus.OPEN)

    # Count commits across every MR in this project
    mr_ids = [mr.id for mr in merge_requests]
    commit_count = (
        db.query(Commit).filter(Commit.merge_request_id.in_(mr_ids)).count()
        if mr_ids else 0
    )

    unresolved_alerts = (
        db.query(Alert)
        .filter(Alert.project_id == project_id, Alert.is_resolved == False)  # noqa: E712
        .count()
    )

    # Unique authors who contributed at least one MR
    contributor_ids = {mr.author_id for mr in merge_requests if mr.author_id}

    return {
        "project_id": str(project_id),
        "project_name": project.name,
        "total_merge_requests": len(merge_requests),
        "open_merge_requests": open_count,
        "total_commits": commit_count,
        "unresolved_alerts": unresolved_alerts,
        "total_contributors": len(contributor_ids),
    }


@router.get("/{project_id}/scores")
def get_scores(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    #Developer scores for a project, sorted highest first. Returns [] if no data.
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    merge_requests = db.query(MergeRequest).filter(MergeRequest.project_id == project_id).all()

    # Accumulate score and MR count per author
    scores: Dict[str, Dict[str, Any]] = {}
    for mr in merge_requests:
        if not mr.author_id:
            continue
        if mr.author_id not in scores:
            author = db.query(User).filter(User.id == mr.author_id).first()
            scores[mr.author_id] = {
                "user_id": str(mr.author_id),
                "name": author.name if author else "Unknown",
                "email": author.email if author else "",
                "total_score": 0.0,
                "merge_request_count": 0,
            }
        scores[mr.author_id]["total_score"] += mr.score or 0.0
        scores[mr.author_id]["merge_request_count"] += 1

    return sorted(scores.values(), key=lambda x: x["total_score"], reverse=True)


@router.get("/{project_id}/timeline")
def get_timeline(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    merge_requests = db.query(MergeRequest).filter(MergeRequest.project_id == project_id).all()

    # Group MR scores by the Monday of their creation week
    weeks: Dict[str, Dict[str, Any]] = {}
    for mr in merge_requests:
        day = mr.created_at.date()
        week_start = (day - timedelta(days=day.weekday())).isoformat()

        if week_start not in weeks:
            weeks[week_start] = {
                "week": week_start,
                "total_score": 0.0,
                "merge_request_count": 0,
            }
        weeks[week_start]["total_score"] += mr.score or 0.0
        weeks[week_start]["merge_request_count"] += 1

    return sorted(weeks.values(), key=lambda x: x["week"])
