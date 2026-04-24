from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class ProjectBase(BaseModel):
    name: str
    repo_url: str
    status: str


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    repo_url: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
