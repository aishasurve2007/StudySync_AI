"""
activity_logs table (spec §10): the append-only read model.

Domain tables (tasks, focus_sessions) are the source of truth for their own
state; activity_logs is a denormalized event stream that the dashboard/score
read with single-table queries (no joins). Everything a metric needs is
embedded in `metadata` at write time. Events are never mutated — a correction
is a new event.

Note: the Python attribute is `event_metadata` but the column is "metadata"
(`metadata` is reserved by SQLAlchemy's declarative Base).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    event_metadata: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    # Composite index for the rolling-window reads (all queries are user + time).
    __table_args__ = (
        Index("ix_activity_logs_user_time", "user_id", "timestamp"),
    )
