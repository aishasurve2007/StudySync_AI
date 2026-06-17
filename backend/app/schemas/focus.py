import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FocusMode


class FocusStartRequest(BaseModel):
    mode: FocusMode
    duration: int = Field(default=25, ge=0, le=600)   # planned minutes (0 for stopwatch)
    task_id: uuid.UUID | None = None


class FocusCompleteRequest(BaseModel):
    # Optional; if omitted we credit the planned duration. Server caps this.
    actual_minutes: int | None = Field(default=None, ge=0, le=1440)


class FocusSessionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    task_id: uuid.UUID | None
    mode: str
    duration: int
    actual_minutes: int
    started_at: datetime
    ended_at: datetime | None
    completed: bool


class ProductivityScore(BaseModel):
    score: int
    task_completion: float
    focus_ratio: float
    consistency: float
    active_days: int
    window_days: int
    total_focus_minutes: int
    completed_tasks: int
    created_tasks: int
