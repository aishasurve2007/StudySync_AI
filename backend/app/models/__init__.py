"""Import every model here so `Base.metadata` is fully populated
(Alembic autogenerate and create_all both rely on this)."""
from app.models.ai_profile import AIProfile
from app.models.student_profile import StudentProfile
from app.models.user import User

__all__ = ["User", "StudentProfile", "AIProfile"]
