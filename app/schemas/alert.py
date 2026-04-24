from datetime import datetime
from pydantic import BaseModel
from typing import Optional
import uuid


class AlertBase(BaseModel):
    type: str
    severity: str
    message: str
    is_resolved: bool = False
class AlertCreate(AlertBase):
    project_id: uuid.UUID


class AlertUpdate(BaseModel):
    type: Optional[str] = None
    severity: Optional[str] = None
    message: Optional[str] = None
    is_resolved: Optional[bool] = None


class AlertResponse(AlertBase):
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
