"""AI Study Coach endpoint (spec §11)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.ai.base import AIProvider
from app.services.ai.factory import get_ai_provider
from app.services.coach import compute_coach_context, generate_insight

router = APIRouter(prefix="/coach", tags=["coach"])


class CoachContext(BaseModel):
    study_minutes: int
    completed_tasks: int
    created_tasks: int
    completed_sessions: int
    started_sessions: int
    missed_sessions: int
    active_days: int
    best_time_of_day: str | None
    best_time_count: int
    window_days: int


class CoachInsight(BaseModel):
    insight: str
    source: str           # "ai" | "fallback"
    context: CoachContext


@router.get("/insight", response_model=CoachInsight)
def get_insight(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    provider: AIProvider = Depends(get_ai_provider),
) -> CoachInsight:
    ctx = compute_coach_context(db, current_user)
    insight, source = generate_insight(ctx, provider)
    return CoachInsight(insight=insight, source=source, context=CoachContext(**ctx))
