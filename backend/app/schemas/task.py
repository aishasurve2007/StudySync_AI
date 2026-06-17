import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TaskPriority


class TaskPlanRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=280)
    deadline_days: int = Field(ge=1, le=365)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_time: int = Field(default=60, ge=5, le=600)
    deadline: datetime | None = None


class TaskPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: str | None
    priority: str
    estimated_time: int
    deadline: datetime | None
    status: str
    created_at: datetime
    completed_at: datetime | None


class TaskPlanResponse(BaseModel):
    source: str               # "ai" | "fallback"
    tasks: list[TaskPublic]
