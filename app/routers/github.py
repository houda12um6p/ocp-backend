from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..core.database import get_db
from ..services.github_service import GitHubService
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/github", tags=["github"])


class SyncRequest(BaseModel):
    repo_owner: str
    repo_name: str
    project_id: uuid.UUID


class BranchResponse(BaseModel):
    name: str
    commit: Dict[str, Any]


@router.post("/sync/commits")
async def sync_commits(sync_request: SyncRequest, db: Session = Depends(get_db)):
    github_service = GitHubService(db)
    try:
        commits = await github_service.sync_commits(
            sync_request.repo_owner,
            sync_request.repo_name,
            sync_request.project_id
        )
        return {"message": f"Synced {len(commits)} commits", "commits_count": len(commits)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync commits: {str(e)}"
        )


@router.post("/sync/pull-requests")
async def sync_pull_requests(sync_request: SyncRequest, db: Session = Depends(get_db)):
    github_service = GitHubService(db)
    try:
        pull_requests = await github_service.sync_pull_requests(
            sync_request.repo_owner,
            sync_request.repo_name,
            sync_request.project_id
        )
        return {"message": f"Synced {len(pull_requests)} pull requests", "prs_count": len(pull_requests)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync pull requests: {str(e)}"
        )


@router.get("/branches", response_model=List[BranchResponse])
async def get_branches(repo_owner: str, repo_name: str, db: Session = Depends(get_db)):
    github_service = GitHubService(db)
    try:
        branches = await github_service.fetch_branches(repo_owner, repo_name)
        return [BranchResponse(**branch) for branch in branches]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch branches: {str(e)}"
        )
