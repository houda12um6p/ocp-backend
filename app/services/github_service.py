from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..models.merge_request import MergeRequest
from ..models.commit import Commit
from ..models.user import User
from ..core.config import settings
import uuid
from datetime import datetime


class GitHubService:
    def __init__(self, db: Session):
        self.db = db
        self.api_url = settings.github_api_url
    async def fetch_commits(self, repo_owner: str, repo_name: str) -> List[Dict[str, Any]]:
        return [
            {
                "sha": "abc123",
                "message": "feat: add user authentication",
                "author": {"email": "john@example.com", "name": "John Doe"},
                "date": "2024-01-01T10:00:00Z"
            },
            {
                "sha": "def456",
                "message": "fix: resolve login bug",
                "author": {"email": "jane@example.com", "name": "Jane Smith"},
                "date": "2024-01-02T15:30:00Z"
            }
        ]

    async def fetch_pull_requests(self, repo_owner: str, repo_name: str) -> List[Dict[str, Any]]:
        return [
            {
                "id": 123,
                "title": "Add user authentication feature [LEAP-24]",
                "author": {"email": "john@example.com", "name": "John Doe"},
                "status": "open",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z"
            },
            {
                "id": 124,
                "title": "Fix login authentication issue",
                "author": {"email": "jane@example.com", "name": "Jane Smith"},
                "status": "merged",
                "created_at": "2024-01-02T15:30:00Z",
                "updated_at": "2024-01-03T09:15:00Z"
            }
        ]

    async def fetch_branches(self, repo_owner: str, repo_name: str) -> List[Dict[str, Any]]:
        return [
            {
                "name": "main",
                "commit": {"sha": "abc123", "url": "https://api.github.com/repos/owner/repo/commits/abc123"}
            },
            {
                "name": "feature/auth",
                "commit": {"sha": "def456", "url": "https://api.github.com/repos/owner/repo/commits/def456"}
            },
            {
                "name": "hotfix/login-bug",
                "commit": {"sha": "ghi789", "url": "https://api.github.com/repos/owner/repo/commits/ghi789"}
            }
        ]

    async def sync_commits(self, repo_owner: str, repo_name: str, project_id: uuid.UUID) -> List[Commit]:
        commits_data = await self.fetch_commits(repo_owner, repo_name)
        synced_commits: List[Commit] = []

        # Commits must belong to a MergeRequest — use the first one found for this project
        merge_request = self.db.query(MergeRequest).filter(MergeRequest.project_id == project_id).first()
        if not merge_request:
            return synced_commits

        for commit_data in commits_data:
            user = self.db.query(User).filter(User.email == commit_data["author"]["email"]).first()
            if not user:
                continue

            # Skip duplicates — sha is the unique identifier for a commit
            if self.db.query(Commit).filter(Commit.sha == commit_data["sha"]).first():
                continue

            commit = Commit(
                sha=commit_data["sha"],
                message=commit_data["message"],
                author_id=user.id,
                merge_request_id=merge_request.id,
                date=datetime.fromisoformat(commit_data["date"].replace("Z", "+00:00")),
            )
            self.db.add(commit)
            synced_commits.append(commit)

        self.db.commit()
        return synced_commits

    async def sync_pull_requests(self, repo_owner: str, repo_name: str, project_id: uuid.UUID) -> List[MergeRequest]:
        prs_data = await self.fetch_pull_requests(repo_owner, repo_name)
        synced_prs = []
        for pr_data in prs_data:
            user = self.db.query(User).filter(User.email == pr_data["author"]["email"]).first()
            if not user:
                user = User(
                    name=pr_data["author"]["name"],
                    email=pr_data["author"]["email"],
                    password_hash="placeholder", 
                    role="developer"
                )
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
            existing_pr = self.db.query(MergeRequest).filter(MergeRequest.github_id == pr_data["id"]).first()
            if existing_pr:
                continue
            # additions + deletions come from the GitHub API; default to 0 if not present
            lines_modified = pr_data.get("additions", 0) + pr_data.get("deletions", 0)
            merge_request = MergeRequest(
                github_id=pr_data["id"],
                title=pr_data["title"],
                author_id=user.id,
                project_id=project_id,
                status=pr_data["status"],
                lines_modified=lines_modified,
                created_at=datetime.fromisoformat(pr_data["created_at"].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(pr_data["updated_at"].replace('Z', '+00:00'))
            )

            self.db.add(merge_request)
            synced_prs.append(merge_request)
        self.db.commit()
        return synced_prs
