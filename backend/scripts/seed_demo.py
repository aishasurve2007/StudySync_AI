"""
Seed a polished demo account so a recruiter opening the live link sees a
populated, alive dashboard instead of an empty one.

Run from the backend directory (with your .env pointing at the target DB):

    python -m scripts.seed_demo

It is idempotent: it deletes any previous demo users first, then recreates
everything with backdated activity over the last 7 days (so the streak,
weekly stats, productivity score, and a grown garden all show real numbers).
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.activity_log import ActivityLog
from app.models.ai_profile import AIProfile
from app.models.enums import EventType, FocusMode, RoomStatus, TaskStatus
from app.models.focus_session import FocusSession
from app.models.student_profile import StudentProfile
from app.models.study_room import RoomMember, StudyRoom
from app.models.task import Task
from app.models.user import User
from app.services.ai.providers import NullProvider
from app.services.gamification import recompute_rewards
from app.services.goal_tags import extract_goal_tags
from app.services.personality import generate_personality

DEMO_EMAIL = "demo@studysync.app"
DEMO_PASSWORD = "demopass123"
PARTNER_EMAIL = "Aisha.demo@studysync.app"

COMPLETED_TASK_TITLES = [
    "Revise linear & logistic regression",
    "Practice 5 LeetCode array problems",
    "Summarise bias-variance tradeoff",
    "Mock interview: ML system design",
    "Read chapter on gradient descent",
    "Implement k-means from scratch",
    "Review confusion matrix & metrics",
    "Flashcards: probability basics",
]
PENDING_TASK_TITLES = [
    "Build a small RAG demo",
    "Write up project README",
    "Time a full mock interview",
]


def _purge(db, email: str) -> None:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        db.delete(user)  # FK ondelete=CASCADE clears profile/tasks/sessions/events/rewards
        db.commit()


def seed() -> None:
    db = SessionLocal()
    try:
        _purge(db, DEMO_EMAIL)
        _purge(db, PARTNER_EMAIL)

        now = datetime.now(timezone.utc)

        # --- demo user + profile ---
        demo = User(
            email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD),
            name="Aisha", timezone="Asia/Kolkata",
        )
        db.add(demo)
        db.flush()

        subjects = ["Machine Learning", "Statistics", "Algorithms"]
        profile = StudentProfile(
            user_id=demo.id, course="Computer Science", year=3, subjects=subjects,
            learning_style="practice", preferred_study_time="evening",
            study_environment="quiet", study_intensity="intensive",
            current_goal="Prepare ML interview",
            goal_tags=extract_goal_tags("Prepare ML interview", subjects),
            daily_goal_hours=3, motivation_type="achievement", experience_level="intermediate",
        )
        db.add(profile)
        db.flush()

        # --- AI personality (deterministic fallback so seeding needs no key) ---
        res = generate_personality(profile, NullProvider())
        db.add(AIProfile(
            user_id=demo.id, personality_type=res.personality_type,
            strengths=res.strengths, weaknesses=res.weaknesses,
            recommendations=res.recommendations,
            recommended_partner_type=res.recommended_partner_type, source=res.source,
        ))

        def log(event_type: EventType, metadata: dict, ts: datetime) -> None:
            db.add(ActivityLog(user_id=demo.id, event_type=event_type.value,
                               event_metadata=metadata, timestamp=ts))

        # --- 7 days of backdated activity: 2 tasks + 2 sessions per day ---
        t_idx = 0
        for d in range(7):
            base = now - timedelta(days=d, hours=2)
            for _ in range(2):
                title = COMPLETED_TASK_TITLES[t_idx % len(COMPLETED_TASK_TITLES)]
                t_idx += 1
                task = Task(user_id=demo.id, title=title, priority="high",
                            estimated_time=60, status=TaskStatus.COMPLETED.value,
                            created_at=base, completed_at=base)
                db.add(task)
                db.flush()
                log(EventType.TASK_CREATED, {"task_id": str(task.id)}, base)
                log(EventType.TASK_COMPLETED, {"task_id": str(task.id)}, base + timedelta(minutes=30))

            for minutes in (45, 50):
                fs = FocusSession(user_id=demo.id, mode=FocusMode.DEEP_WORK.value,
                                  duration=minutes, actual_minutes=minutes, completed=True,
                                  started_at=base, ended_at=base + timedelta(minutes=minutes))
                db.add(fs)
                db.flush()
                log(EventType.SESSION_STARTED, {"session_id": str(fs.id), "mode": fs.mode}, base)
                log(EventType.SESSION_COMPLETED,
                    {"session_id": str(fs.id), "mode": fs.mode, "actual_minutes": minutes},
                    base + timedelta(minutes=minutes))

        # --- a few pending tasks for today ---
        for title in PENDING_TASK_TITLES:
            task = Task(user_id=demo.id, title=title, priority="medium",
                        estimated_time=90, status=TaskStatus.PENDING.value, created_at=now)
            db.add(task)
            db.flush()
            log(EventType.TASK_CREATED, {"task_id": str(task.id)}, now)

        # --- an active study room ---
        room = StudyRoom(created_by=demo.id, subject="Machine Learning Study Group",
                         max_users=8, status=RoomStatus.ACTIVE.value, created_at=now)
        db.add(room)
        db.flush()
        db.add(RoomMember(room_id=room.id, user_id=demo.id))
        log(EventType.ROOM_JOINED, {"room_id": str(room.id)}, now)

        # --- XP / garden from the activity ---
        recompute_rewards(db, demo)

        # --- a second user so the Partners page has a real match ---
        partner = User(email=PARTNER_EMAIL, password_hash=hash_password(DEMO_PASSWORD),
                       name="AishaS", timezone="Asia/Kolkata")
        db.add(partner)
        db.flush()
        p_subjects = ["Machine Learning", "Statistics"]
        db.add(StudentProfile(
            user_id=partner.id, course="Computer Science", year=3, subjects=p_subjects,
            learning_style="practice", preferred_study_time="evening",
            study_environment="discussion", study_intensity="intensive",
            current_goal="Machine learning revision",
            goal_tags=extract_goal_tags("Machine learning revision", p_subjects),
            daily_goal_hours=2, motivation_type="growth", experience_level="intermediate",
        ))

        db.commit()

        rewards = recompute_rewards(db, demo)
        db.commit()
        print("Demo account seeded.")
        print(f"  login: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print(f"  garden: {rewards.garden_stage}  ({rewards.xp} XP, level {rewards.level})")
        print(f"  partner match available: {partner.name}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
