"""
Matching endpoints (spec §4).

  GET /matches?limit=10                  -> ranked compatible partners (no AI)
  GET /matches/{partner_id}/explanation  -> AI 'why you match' for one partner

The list is a fast deterministic query. The natural-language explanation is
generated lazily, one partner at a time, so the AI is only called when the
user actually opens a match — bounding cost and latency.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.match import (
    MatchComponentsOut,
    MatchExplanationOut,
    MatchOut,
    MatchPartner,
)
from app.services.ai.base import AIProvider
from app.services.ai.factory import get_ai_provider
from app.services.matching import compute_compatibility, explain_match, rank_matches

router = APIRouter(prefix="/matches", tags=["matching"])


def _require_profile(db: Session, user_id) -> StudentProfile:
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Create a student profile first (POST /profiles).",
        )
    return profile


@router.get("", response_model=list[MatchOut])
def list_matches(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MatchOut]:
    me = _require_profile(db, current_user.id)
    ranked = rank_matches(db, me, limit=limit)

    out: list[MatchOut] = []
    for other, score in ranked:
        partner_user = db.get(User, other.user_id)
        out.append(
            MatchOut(
                partner=MatchPartner(
                    user_id=other.user_id,
                    name=partner_user.name if partner_user else "Unknown",
                    avatar=partner_user.avatar if partner_user else None,
                    course=other.course,
                ),
                score=score.score,
                components=MatchComponentsOut(**score.components.__dict__),
                reasons=score.reasons,
                shared_subjects=score.shared_subjects,
                shared_goal_tags=score.shared_goal_tags,
            )
        )
    return out


@router.get("/{partner_id}/explanation", response_model=MatchExplanationOut)
def explanation(
    partner_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    provider: AIProvider = Depends(get_ai_provider),
) -> MatchExplanationOut:
    me = _require_profile(db, current_user.id)
    other = db.scalar(select(StudentProfile).where(StudentProfile.user_id == partner_id))
    if other is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner has no profile.")

    score = compute_compatibility(me, other)
    text, source = explain_match(me, other, score, provider)
    return MatchExplanationOut(
        partner_id=partner_id, score=score.score, explanation=text, source=source
    )
