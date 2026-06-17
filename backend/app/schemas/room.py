import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoomCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=120)
    max_users: int = Field(default=8, ge=2, le=50)


class RoomMemberOut(BaseModel):
    user_id: uuid.UUID
    name: str
    joined_at: datetime


class RoomSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject: str
    max_users: int
    status: str
    created_by: uuid.UUID
    created_at: datetime
    member_count: int


class RoomDetail(RoomSummary):
    members: list[RoomMemberOut]
