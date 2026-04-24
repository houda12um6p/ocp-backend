from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from ..models.jira_task import JiraTask
from ..core.config import settings
from datetime import datetime


class JiraService:
    def __init__(self, db: Session):
        self.db = db
        self.api_url = settings.jira_api_url
    async def fetch_tasks(self, project_key: str) -> List[Dict[str, Any]]:
        return [
            {
                "key": "LEAP-24",
                "title": "Implement user authentication",
                "status": "In Progress",
                "story_points": 5,
                "created_at": "2024-01-01T09:00:00Z",
                "updated_at": "2024-01-01T09:00:00Z"
            },
            {
                "key": "LEAP-25",
                "title": "Fix login page bug",
                "status": "Done",
                "story_points": 3,
                "created_at": "2024-01-02T10:30:00Z",
                "updated_at": "2024-01-03T16:45:00Z"
            },
            {
                "key": "LEAP-26",
                "title": "Add user profile page",
                "status": "To Do",
                "story_points": 8,
                "created_at": "2024-01-04T14:15:00Z",
                "updated_at": "2024-01-04T14:15:00Z"
            }
        ]

    async def fetch_sprints(self, board_id: str) -> List[Dict[str, Any]]:
        return [
            {
                "id": 123,
                "name": "Sprint 1",
                "state": "active",
                "start_date": "2024-01-01T09:00:00Z",
                "end_date": "2024-01-15T17:00:00Z",
                "goal": "Complete authentication features"
            },
            {
                "id": 124,
                "name": "Sprint 2",
                "state": "future",
                "start_date": "2024-01-16T09:00:00Z",
                "end_date": "2024-01-30T17:00:00Z",
                "goal": "Implement user management"
            }
        ]
    async def sync_tasks(self, project_key: str) -> List[JiraTask]:
        tasks_data = await self.fetch_tasks(project_key)
        synced_tasks = []

        for task_data in tasks_data:
            existing_task = self.db.query(JiraTask).filter(JiraTask.jira_key == task_data["key"]).first()
            if existing_task:
                existing_task.title = task_data["title"]
                existing_task.status = task_data["status"]
                existing_task.story_points = task_data["story_points"]
                existing_task.updated_at = datetime.fromisoformat(task_data["updated_at"].replace('Z', '+00:00'))
                synced_tasks.append(existing_task)
            else:
                jira_task = JiraTask(
                    jira_key=task_data["key"],
                    title=task_data["title"],
                    status=task_data["status"],
                    story_points=task_data["story_points"],
                    created_at=datetime.fromisoformat(task_data["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(task_data["updated_at"].replace('Z', '+00:00'))
                )
                self.db.add(jira_task)
                synced_tasks.append(jira_task)

        self.db.commit()
        return synced_tasks

    def find_jira_task_by_key(self, jira_key: str) -> Optional[JiraTask]:
        return self.db.query(JiraTask).filter(JiraTask.jira_key == jira_key).first()

    def link_merge_request_to_jira_task(self, merge_request_id: str, jira_key: str) -> bool:
        jira_task = self.find_jira_task_by_key(jira_key)
        if not jira_task:
            return False
        from ..models.merge_request import MergeRequest
        merge_request = self.db.query(MergeRequest).filter(MergeRequest.id == merge_request_id).first()
        if not merge_request:
            return False
        merge_request.jira_task_id = jira_task.id
        self.db.commit()
        return True
