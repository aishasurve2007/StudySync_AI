"""
Productivity score (spec §8).

Computed entirely from `activity_logs` (single table, no joins), over a rolling
7-day window, with day boundaries in the USER'S timezone:

    task_completion = completed_tasks / max(created_tasks, 1)   (capped 1.0)
    focus_ratio     = min(total_focus_minutes / (daily_goal_hours*60*7), 1.0)
    consistency     = active_days_in_last_7 / 7

    score = round(task_completion*40 + focus_ratio*40 + consistency*20)

An "active day" = a calendar day (user tz) with >= 1 TASK_COMPLETED or
SESSION_COMPLETED event. Only completed sessions contribute focus minutes,
because only completed sessions ever emit SESSION_COMPLETED (§8 anti-abuse).

Window semantics (pinned): created/completed tasks are counted by the
*event timestamp*, so a task created before the window but completed inside it
counts as completed-not-created — which is exactly why task_completion is capped
at 1.0.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.enums import EventType
from app.models.student_profile import StudentProfile
from app.models.user import User

WINDOW_DAYS = 7
DEFAULT_DAILY_GOAL_HOURS = 2.0


def _tz(user: User) -> ZoneInfo:
    try:
        return ZoneInfo(user.timezone)
    except Exception:
        return ZoneInfo("UTC")


def _local_date(ts: datetime, tz: ZoneInfo):
    if ts.tzinfo is None:           # SQLite may return naive datetimes; treat as UTC
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(tz).date()


def compute_productivity(db: Session, user: User) -> dict:
    tz = _tz(user)
    today = datetime.now(tz).date()
    start_date = today - timedelta(days=WINDOW_DAYS - 1)

    # Bound the row scan in UTC (coarse), then bucket precisely by tz in Python.
    utc_cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS + 1)
    events = db.scalars(
        select(ActivityLog)
        .where(ActivityLog.user_id == user.id)
        .where(ActivityLog.timestamp >= utc_cutoff)
    ).all()

    in_window = [e for e in events if start_date <= _local_date(e.timestamp, tz) <= today]

    created = sum(1 for e in in_window if e.event_type == EventType.TASK_CREATED)
    completed = sum(1 for e in in_window if e.event_type == EventType.TASK_COMPLETED)
    focus_minutes = sum(
        int((e.event_metadata or {}).get("actual_minutes", 0))
        for e in in_window if e.event_type == EventType.SESSION_COMPLETED
    )
    active_days = {
        _local_date(e.timestamp, tz)
        for e in in_window
        if e.event_type in (EventType.TASK_COMPLETED, EventType.SESSION_COMPLETED)
    }

    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    daily_goal_hours = profile.daily_goal_hours if profile and profile.daily_goal_hours else DEFAULT_DAILY_GOAL_HOURS

    task_completion = min(completed / max(created, 1), 1.0)
    focus_target = daily_goal_hours * 60 * WINDOW_DAYS
    focus_ratio = min(focus_minutes / focus_target, 1.0) if focus_target > 0 else 0.0
    consistency = len(active_days) / WINDOW_DAYS

    score = round(task_completion * 40 + focus_ratio * 40 + consistency * 20)

    return {
        "score": score,
        "task_completion": round(task_completion, 3),
        "focus_ratio": round(focus_ratio, 3),
        "consistency": round(consistency, 3),
        "active_days": len(active_days),
        "window_days": WINDOW_DAYS,
        "total_focus_minutes": focus_minutes,
        "completed_tasks": completed,
        "created_tasks": created,
    }
