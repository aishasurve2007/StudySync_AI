"""
Event logging helper.

`log_event` adds an ActivityLog row to the CURRENT session but does NOT
commit. The caller commits once, so the domain write (e.g. marking a task
completed) and its event (TASK_COMPLETED) land atomically — either both
persist or neither does. This is what keeps the read model (§10) consistent
with the source-of-truth tables.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.enums import EventType


def log_event(db: Session, user_id: uuid.UUID, event_type: EventType, metadata: dict) -> ActivityLog:
    event = ActivityLog(
        user_id=user_id,
        event_type=event_type.value,
        event_metadata=metadata,
    )
    db.add(event)  # intentionally NOT committed — joins the caller's transaction
    return event
