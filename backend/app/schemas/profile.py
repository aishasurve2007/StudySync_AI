"""
Profile schemas = the questionnaire contract (spec §2).

`goal_tags` is intentionally absent from the input schema: the client cannot
set it. It appears only in the output schema, computed by the backend.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    ExperienceLevel,
    LearningStyle,
    MotivationType,
    StudyEnvironment,
    StudyIntensity,
    StudyTime,
)


class ProfileInput(BaseModel):
    """Used for both create and update (full replace of profile fields)."""
    course: str = Field(min_length=1, max_length=160)
    year: int | None = Field(default=None, ge=1, le=12)

    subjects: list[str] = Field(default_factory=list, max_length=20)
    learning_style: LearningStyle
    preferred_study_time: StudyTime
    study_environment: StudyEnvironment

    study_intensity: StudyIntensity
    current_goal: str | None = Field(default=None, max_length=280)

    daily_goal_hours: float = Field(default=2.0, gt=0, le=24)

    motivation_type: MotivationType | None = None
    experience_level: ExperienceLevel | None = None


class ProfilePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    course: str
    year: int | None
    subjects: list[str]
    learning_style: str
    preferred_study_time: str
    study_environment: str
    study_intensity: str
    current_goal: str | None
    goal_tags: list[str]          # derived by the backend
    daily_goal_hours: float
    motivation_type: str | None
    experience_level: str | None
    created_at: datetime
    updated_at: datetime
