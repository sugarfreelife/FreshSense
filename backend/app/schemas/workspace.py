from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


WorkspaceRole = Literal["owner", "manager", "staff"]


class BusinessWorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class BusinessWorkspaceOut(BaseModel):
    id: str
    name: str
    role: WorkspaceRole
    created_at: datetime


class WorkspaceMemberCreate(BaseModel):
    email: EmailStr
    role: Literal["manager", "staff"] = "staff"


class WorkspaceMemberOut(BaseModel):
    id: str
    user_id: str
    email: EmailStr
    name: str | None
    role: WorkspaceRole
    created_at: datetime
