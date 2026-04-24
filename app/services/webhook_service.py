import re
import logging
from datetime import datetime
from typing import Dict, Any

from sqlalchemy.orm import Session

from ..models.jira_task import JiraTask
from ..services.jira_service import JiraService
from ..services.llm_service import classify_comment

logger = logging.getLogger(__name__)


class WebhookService:
    def __init__(self, db: Session):
        self.db = db
        self.jira_service = JiraService(db)

    async def handle_github_push(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            repo_name = payload.get("repository", {}).get("name")
            commits = payload.get("commits", [])

            processed_commits = []
            for commit_data in commits:
                sha = commit_data.get("id")
                message = commit_data.get("message")
                processed_commits.append({
                    "sha": sha,
                    "message": message,
                    "processed": True
                })
            return {
                "status": "success",
                "repo": repo_name,
                "commits_processed": len(processed_commits)
            }
        except Exception as e:
            logger.error(f"Error handling GitHub push webhook: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def handle_github_pull_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            action = payload.get("action")
            pr_data = payload.get("pull_request", {})

            if action in ["opened", "synchronize", "reopened", "closed"]:
                github_id = pr_data.get("id")
                title = pr_data.get("title")
                jira_key = None
                pattern = r'([A-Z]+-\d+)'
                match = re.search(pattern, title)
                if match:
                    jira_key = match.group(1)
                return {
                    "status": "success",
                    "action": action,
                    "pr_id": github_id,
                    "title": title,
                    "jira_key_extracted": jira_key
                }

            return {"status": "ignored", "action": action}
        except Exception as e:
            logger.error(f"Error handling GitHub PR webhook: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def handle_github_review_comment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            action = payload.get("action")
            comment_data = payload.get("comment", {})
            pr_data = payload.get("pull_request", {})

            if action in ["created", "edited", "deleted"]:
                body = comment_data.get("body", "")
                pr_id = pr_data.get("id")
                severity_weight = await classify_comment(body) if action != "deleted" else 0
                return {
                    "status": "success",
                    "action": action,
                    "pr_id": pr_id,
                    "severity_weight": severity_weight,
                    "comment_length": len(body)
                }

            return {"status": "ignored", "action": action}
        except Exception as e:
            logger.error(f"Error handling GitHub review comment webhook: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def handle_jira_issue_updated(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            issue_data = payload.get("issue", {})
            jira_key = issue_data.get("key")
            title = issue_data.get("fields", {}).get("summary")
            status = issue_data.get("fields", {}).get("status", {}).get("name")
            jira_task = self.jira_service.find_jira_task_by_key(jira_key)
            if jira_task:
                jira_task.title = title
                jira_task.status = status
                jira_task.updated_at = datetime.utcnow()
                self.db.commit()
                return {
                    "status": "success",
                    "action": "updated",
                    "jira_key": jira_key,
                    "new_status": status
                }
            else:
                new_task = JiraTask(
                    jira_key=jira_key,
                    title=title,
                    status=status,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(new_task)
                self.db.commit()
                return {
                    "status": "success",
                    "action": "created",
                    "jira_key": jira_key,
                    "task_id": str(new_task.id)
                }
        except Exception as e:
            logger.error(f"Error handling Jira issue webhook: {str(e)}")
            return {"status": "error", "message": str(e)}
