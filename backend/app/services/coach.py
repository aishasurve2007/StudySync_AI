"""
AI Study Coach (spec §11).

The backend computes the student's last-7-days facts from `activity_logs`
(study minutes, completed/created tasks, started vs completed sessions ->
"missed", active days, and the time-of-day where most sessions complete). The
AI then writes ONE short, specific insight grounded in those numbers. As
everywhere, there's a deterministic fallback insight so the coach works with no
API key — and the AI can't invent stats because we only hand it the computed
facts.
"""
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.enums import EventType, StudyTime
from app.models.user import User
from app.services.productivity import WINDOW_DAYS, _local_date, _tz


def _bucket_for_hour(hour: int) -> StudyTime:
    if 5 <= hour <= 11:
        return StudyTime.MORNING
    if 12 <= hour <= 16:
        return StudyTime.AFTERNOON
    if 17 <= hour <= 21:
        return StudyTime.EVENING
    return StudyTime.NIGHT


def compute_coach_context(db: Session, user: User) -> dict:
    tz = _tz(user)
    today = datetime.now(tz).date()
    start = today - timedelta(days=WINDOW_DAYS - 1)
    utc_cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS + 1)

    events = db.scalars(
        select(ActivityLog)
        .where(ActivityLog.user_id == user.id)
        .where(ActivityLog.timestamp >= utc_cutoff)
    ).all()

    study_minutes = completed_tasks = created_tasks = 0
    started_sessions = completed_sessions = 0
    active_dates: set = set()
    bucket_counts: dict = {b: 0 for b in StudyTime}

    for e in events:
        ts = e.timestamp if e.timestamp.tzinfo else e.timestamp.replace(tzinfo=timezone.utc)
        d = _local_date(ts, tz)
        if not (start <= d <= today):
            continue
        if e.event_type in (EventType.TASK_COMPLETED, EventType.SESSION_COMPLETED):
            active_dates.add(d)
        if e.event_type == EventType.SESSION_COMPLETED:
            completed_sessions += 1
            study_minutes += int((e.event_metadata or {}).get("actual_minutes", 0))
            bucket_counts[_bucket_for_hour(ts.astimezone(tz).hour)] += 1
        elif e.event_type == EventType.SESSION_STARTED:
            started_sessions += 1
        elif e.event_type == EventType.TASK_COMPLETED:
            completed_tasks += 1
        elif e.event_type == EventType.TASK_CREATED:
            created_tasks += 1

    best_bucket, best_count = None, 0
    for b, c in bucket_counts.items():
        if c > best_count:
            best_bucket, best_count = b.value, c

    return {
        "study_minutes": study_minutes,
        "completed_tasks": completed_tasks,
        "created_tasks": created_tasks,
        "completed_sessions": completed_sessions,
        "started_sessions": started_sessions,
        "missed_sessions": max(started_sessions - completed_sessions, 0),
        "active_days": len(active_dates),
        "best_time_of_day": best_bucket,
        "best_time_count": best_count,
        "window_days": WINDOW_DAYS,
    }


def _fallback_insight(ctx: dict) -> str:
    if ctx["completed_tasks"] == 0 and ctx["started_sessions"] == 0:
        return "No activity logged in the last 7 days yet — start with one small task today to get your garden growing."
    if ctx["started_sessions"] > 0 and ctx["completed_sessions"] == 0:
        return "You started focus sessions but finished none — try shorter blocks (around 15 minutes) you can actually complete."
    if ctx["missed_sessions"] >= 2:
        return f"You left {ctx['missed_sessions']} sessions unfinished this week — a shorter Pomodoro may help you finish what you start."
    if ctx["best_time_of_day"] and ctx["best_time_count"] >= 2:
        return f"You complete most of your focus sessions in the {ctx['best_time_of_day']} — schedule your hardest topics then."
    if ctx["completed_tasks"] > 0 and ctx["completed_sessions"] == 0:
        return "You're checking off tasks but not logging focus time — try one timed deep-work block to build momentum."
    if ctx["active_days"] >= 5:
        return f"Strong consistency — {ctx['active_days']} active days this week. Keep the streak going."
    return f"This week: {ctx['completed_tasks']} tasks done and {ctx['study_minutes']} minutes focused. Pick one priority for tomorrow and protect the time."


def generate_insight(ctx: dict, provider) -> tuple[str, str]:
    fallback = _fallback_insight(ctx)
    system = (
        "You are a supportive study coach. Given a student's last-7-days stats, "
        "write ONE short, specific, encouraging insight (max 30 words) grounded "
        "ONLY in these numbers — do not invent data. Reply as JSON: "
        '{"insight": str}.'
    )
    raw = provider.complete_json(system, json.dumps(ctx))
    if isinstance(raw, dict) and isinstance(raw.get("insight"), str) and raw["insight"].strip():
        return raw["insight"].strip()[:300], "ai"
    return fallback, "fallback"
