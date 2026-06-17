"""
XP + garden gamification (spec §9).

XP is a deterministic function of completion events, with per-day caps applied
so it can't be farmed:
    task completion   +10
    focus session     +20   (max 6 rewarded sessions/day)
    daily streak      +50   (any day with activity)
    daily XP cap      200

Because XP is derived from the immutable event log, recomputing is idempotent —
calling recompute twice yields the same number, so there's no double-counting.

Garden stages by total XP:
    0 Seed · 100 Sprout · 300 Flower · 700 Tree · 1500 Fruit Tree
"""
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.enums import EventType
from app.models.user import User
from app.models.user_rewards import UserRewards
from app.services.productivity import _local_date, _tz

XP_TASK = 10
XP_SESSION = 20
XP_STREAK = 50
MAX_REWARDED_SESSIONS = 6
DAILY_XP_CAP = 200

STAGES: list[tuple[int, str]] = [
    (0, "Seed"),
    (100, "Sprout"),
    (300, "Flower"),
    (700, "Tree"),
    (1500, "Fruit Tree"),
]


def compute_xp(db: Session, user: User) -> int:
    tz = _tz(user)
    events = db.scalars(select(ActivityLog).where(ActivityLog.user_id == user.id)).all()

    tasks_by_day: dict = defaultdict(int)
    sessions_by_day: dict = defaultdict(int)
    for e in events:
        if e.event_type == EventType.TASK_COMPLETED:
            tasks_by_day[_local_date(e.timestamp, tz)] += 1
        elif e.event_type == EventType.SESSION_COMPLETED:
            sessions_by_day[_local_date(e.timestamp, tz)] += 1

    total = 0
    for day in set(tasks_by_day) | set(sessions_by_day):
        t = tasks_by_day[day]
        s = sessions_by_day[day]
        active = (t > 0) or (s > 0)
        day_xp = (
            t * XP_TASK
            + min(s, MAX_REWARDED_SESSIONS) * XP_SESSION
            + (XP_STREAK if active else 0)
        )
        total += min(day_xp, DAILY_XP_CAP)
    return total


def level_and_stage(xp: int) -> tuple[int, str, str | None, int | None]:
    level, stage = 1, STAGES[0][1]
    for i, (threshold, name) in enumerate(STAGES):
        if xp >= threshold:
            level, stage = i + 1, name
    next_stage, xp_to_next = None, None
    for threshold, name in STAGES:
        if xp < threshold:
            next_stage, xp_to_next = name, threshold - xp
            break
    return level, stage, next_stage, xp_to_next


def recompute_rewards(db: Session, user: User) -> UserRewards:
    """Recompute XP from events and upsert user_rewards. Does NOT commit —
    joins the caller's transaction (so it stays atomic with a completion)."""
    db.flush()  # make any pending events visible to the query within this txn
    xp = compute_xp(db, user)
    level, stage, _, _ = level_and_stage(xp)

    row = db.scalar(select(UserRewards).where(UserRewards.user_id == user.id))
    if row is None:
        row = UserRewards(user_id=user.id)
        db.add(row)
    row.xp = xp
    row.level = level
    row.garden_stage = stage
    return row
