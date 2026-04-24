from datetime import datetime
from pydantic import BaseModel
from typing import Optional
try:
    from pydantic import EmailStr
except ImportError:
    EmailStr = str  # type: ignore[assignment, misc]
    
from ..models.user import UserRole


class UserBase(BaseModel):
    name: str
    email: str  
    role: UserRole = UserRole.DEVELOPER
class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    total_score: Optional[float] = None

class UserResponse(UserBase):
    id: str  # stored as String(36) in SQLite
    total_score: float
    created_at: datetime

    class Config:
        from_attributes =True

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
