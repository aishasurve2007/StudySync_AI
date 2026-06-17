"""
Weekly activity report (spec §10).

Every metric is a single-table read over `activity_logs`, bucketed by the
user's timezone:
    study_minutes   = Σ metadata.actual_minutes of SESSION_COMPLETED (last 7d)
    tasks_completed = count of TASK_COMPLETED (last 7d)
    focus_sessions  = count of SESSION_COMPLETED (last 7d)
    consistency     = active_days_in_last_7 / 7   (§8 definition)
    current_streak  = consecutive active days up to today

`study_minutes` reads `actual_minutes` straight out of each event's metadata —
no join back to focus_sessions — which is the whole point of embedding it at
write time (§10).
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.enums import EventType
from app.models.user import User
from app.services.productivity import WINDOW_DAYS, _local_date, _tz


def weekly_report(db: Session, user: User) -> dict:
    tz = _tz(user)
    today = datetime.now(tz).date()
    week_start = today - timedelta(days=WINDOW_DAYS - 1)

    # Fetch a wider window than 7 days so the streak can extend beyond the week.
    utc_cutoff = datetime.now(timezone.utc) - timedelta(days=120)
    events = db.scalars(
        select(ActivityLog)
        .where(ActivityLog.user_id == user.id)
        .where(ActivityLog.timestamp >= utc_cutoff)
    ).all()

    study_minutes = 0
    tasks_completed = 0
    focus_sessions = 0
    active_dates: set = set()

    for e in events:
        d = _local_date(e.timestamp, tz)
        is_active_event = e.event_type in (EventType.TASK_COMPLETED, EventType.SESSION_COMPLETED)
        if is_active_event:
            active_dates.add(d)
        if not (week_start <= d <= today):
            continue
        if e.event_type == EventType.SESSION_COMPLETED:
            focus_sessions += 1
            study_minutes += int((e.event_metadata or {}).get("actual_minutes", 0))
        elif e.event_type == EventType.TASK_COMPLETED:
            tasks_completed += 1

    active_in_week = {d for d in active_dates if week_start <= d <= today}
    consistency = len(active_in_week) / WINDOW_DAYS

    # Current streak: consecutive active days ending today (with a one-day grace
    # so an in-progress day with no activity yet doesn't break yesterday's run).
    streak = 0
    cursor = today
    if today not in active_dates and (today - timedelta(days=1)) in active_dates:
        cursor = today - timedelta(days=1)
    while cursor in active_dates:
        streak += 1
        cursor -= timedelta(days=1)

    return {
        "study_minutes": study_minutes,
        "tasks_completed": tasks_completed,
        "focus_sessions": focus_sessions,
        "current_streak": streak,
        "active_days": len(active_in_week),
        "consistency": round(consistency, 3),
        "consistency_pct": round(consistency * 100),
        "window_days": WINDOW_DAYS,
    }
