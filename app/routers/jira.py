from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..services.jira_service import JiraService
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/jira", tags=["jira"])
class SyncRequest(BaseModel):
    project_key: str
class SprintResponse(BaseModel):
    id: int
    name: str
    state: str
    start_date: str
    end_date: str
    goal: str


class LinkRequest(BaseModel):
    merge_request_id: uuid.UUID
    jira_key: str


@router.post("/sync/tasks")
async def sync_tasks(sync_request: SyncRequest, db: Session = Depends(get_db)):
    jira_service = JiraService(db)
    try:
        tasks = await jira_service.sync_tasks(sync_request.project_key)
        return {"message": f"Synced {len(tasks)} tasks", "tasks_count": len(tasks)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync tasks: {str(e)}"
        )


@router.get("/sprints", response_model=List[SprintResponse])
async def get_sprints(board_id: str, db: Session = Depends(get_db)):
    jira_service = JiraService(db)
    try:
        sprints = await jira_service.fetch_sprints(board_id)
        return [SprintResponse(**sprint) for sprint in sprints]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sprints: {str(e)}"
        )


@router.post("/link")
async def link_merge_request_to_task(link_request: LinkRequest, db: Session = Depends(get_db)):
    
    jira_service = JiraService(db)
    try:
        success = jira_service.link_merge_request_to_jira_task(
            link_request.merge_request_id,
            link_request.jira_key
        )
        if success:
            return {"message": "Merge request linked to Jira task successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Merge request or Jira task not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link merge request to Jira task: {str(e)}"
        )
