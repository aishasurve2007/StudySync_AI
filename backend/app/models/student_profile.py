"""
student_profiles table (spec §2): HOW a student studies (not auth data).

Notes:
- Array columns use Postgres native arrays in production (GIN-indexable for
  the matching pre-filter in §4) and fall back to JSON on SQLite for tests,
  via `.with_variant(...)`.
- `goal_tags` is written by `extract_goal_tags` on create/update, never by
  the client and never by the AI. It is non-null after creation.
- One profile per user => `user_id` is unique.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import ARRAY, Float, ForeignKey, Integer, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# Postgres text[] in prod; JSON on SQLite so the same model runs in tests.
_StrArray = ARRAY(String).with_variant(JSON, "sqlite")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, index=True, nullable=False,
    )

    course: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # used by matching (subject_match): Jaccard over these sets
    subjects: Mapped[list[str]] = mapped_column(_StrArray, nullable=False, default=list)

    learning_style: Mapped[str] = mapped_column(String(32), nullable=False)
    preferred_study_time: Mapped[str] = mapped_column(String(32), nullable=False)
    study_environment: Mapped[str] = mapped_column(String(32), nullable=False)

    study_intensity: Mapped[str] = mapped_column(String(32), nullable=False)  # matching (ordinal)
    current_goal: Mapped[str | None] = mapped_column(String(280), nullable=True)
    # derived deterministically from current_goal + subjects; never client-set
    goal_tags: Mapped[list[str]] = mapped_column(_StrArray, nullable=False, default=list)

    daily_goal_hours: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)

    motivation_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(32), nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow, onupdate=_utcnow, nullable=False)
