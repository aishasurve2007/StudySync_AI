import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.focus import ProductivityScore


class RewardsPublic(BaseModel):
    user_id: uuid.UUID
    xp: int
    level: int
    garden_stage: str
    next_stage: str | None
    xp_to_next: int | None
    updated_at: datetime


class WeeklyReport(BaseModel):
    study_minutes: int
    tasks_completed: int
    focus_sessions: int
    current_streak: int
    active_days: int
    consistency: float
    consistency_pct: int
    window_days: int


class DashboardSummary(BaseModel):
    name: str
    has_profile: bool
    personality_type: str | None
    productivity: ProductivityScore
    rewards: RewardsPublic
    weekly: WeeklyReport
