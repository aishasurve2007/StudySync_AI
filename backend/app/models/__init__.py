"""Import every model here so `Base.metadata` is fully populated
(Alembic autogenerate and create_all both rely on this)."""
from app.models.activity_log import ActivityLog
from app.models.ai_profile import AIProfile
from app.models.focus_session import FocusSession
from app.models.student_profile import StudentProfile
from app.models.study_room import RoomMember, StudyRoom
from app.models.task import Task
from app.models.user import User
from app.models.user_rewards import UserRewards

__all__ = [
    "User", "StudentProfile", "AIProfile",
    "Task", "FocusSession", "ActivityLog", "UserRewards",
    "StudyRoom", "RoomMember",
]
