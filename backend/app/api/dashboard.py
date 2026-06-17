"""
Gamification + analytics + dashboard endpoints (spec §9, §10, + Phase 1 dashboard).

  GET /rewards           -> XP, level, garden stage (+ progress to next stage)
  GET /analytics/weekly  -> weekly report (single-table reads over activity_logs)
  GET /dashboard         -> one call composing the above for the home screen
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.ai_profile import AIProfile
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, RewardsPublic, WeeklyReport
from app.schemas.focus import ProductivityScore
from app.services.analytics import weekly_report
from app.services.gamification import level_and_stage, recompute_rewards
from app.services.productivity import compute_productivity

router = APIRouter(tags=["dashboard"])


def _rewards_payload(db: Session, user: User) -> RewardsPublic:
    row = recompute_rewards(db, user)
    db.commit()
    db.refresh(row)
    _, _, next_stage, xp_to_next = level_and_stage(row.xp)
    return RewardsPublic(
        user_id=row.user_id, xp=row.xp, level=row.level, garden_stage=row.garden_stage,
        next_stage=next_stage, xp_to_next=xp_to_next, updated_at=row.updated_at,
    )


@router.get("/rewards", response_model=RewardsPublic)
def get_rewards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RewardsPublic:
    return _rewards_payload(db, current_user)


@router.get("/analytics/weekly", response_model=WeeklyReport)
def get_weekly(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WeeklyReport:
    return WeeklyReport(**weekly_report(db, current_user))


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardSummary:
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    ai_profile = db.scalar(select(AIProfile).where(AIProfile.user_id == current_user.id))

    return DashboardSummary(
        name=current_user.name,
        has_profile=profile is not None,
        personality_type=ai_profile.personality_type if ai_profile else None,
        productivity=ProductivityScore(**compute_productivity(db, current_user)),
        rewards=_rewards_payload(db, current_user),
        weekly=WeeklyReport(**weekly_report(db, current_user)),
    )
