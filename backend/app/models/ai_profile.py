"""
ai_profiles table (spec §3): the generated learning personality.

One row per user (regenerating overwrites it). Arrays use the same
Postgres-text[] / SQLite-JSON variant as the rest of the app. `source`
records whether the AI layer produced this or the deterministic fallback
did — useful for the demo and for debugging an AI outage.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import ARRAY, ForeignKey, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

_StrArray = ARRAY(String).with_variant(JSON, "sqlite")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AIProfile(Base):
    __tablename__ = "ai_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, index=True, nullable=False,
    )

    personality_type: Mapped[str] = mapped_column(String(80), nullable=False)
    strengths: Mapped[list[str]] = mapped_column(_StrArray, nullable=False, default=list)
    weaknesses: Mapped[list[str]] = mapped_column(_StrArray, nullable=False, default=list)
    recommendations: Mapped[list[str]] = mapped_column(_StrArray, nullable=False, default=list)
    recommended_partner_type: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="fallback")

    created_at: Mapped[datetime] = mapped_column(default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow, onupdate=_utcnow, nullable=False)
