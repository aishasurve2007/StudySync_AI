"""
AI personality endpoints (spec §3).

  POST /ai/personality  -> generate (or regenerate) from the student profile
  GET  /ai/personality  -> fetch the stored personality

Generation requires a student profile (404 otherwise). The AI provider is
injected as a dependency so it can be swapped/mocked; whatever happens, the
deterministic fallback guarantees a grounded result.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.ai_profile import AIProfile
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.ai_profile import AIProfilePublic
from app.services.ai.base import AIProvider
from app.services.ai.factory import get_ai_provider
from app.services.personality import generate_personality

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/personality", response_model=AIProfilePublic, status_code=status.HTTP_201_CREATED)
def generate(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    provider: AIProvider = Depends(get_ai_provider),
) -> AIProfilePublic:
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Create a student profile first (POST /profiles).",
        )

    result = generate_personality(profile, provider)

    ai_profile = db.scalar(select(AIProfile).where(AIProfile.user_id == current_user.id))
    if ai_profile is None:
        ai_profile = AIProfile(user_id=current_user.id)
        db.add(ai_profile)

    ai_profile.personality_type = result.personality_type
    ai_profile.strengths = result.strengths
    ai_profile.weaknesses = result.weaknesses
    ai_profile.recommendations = result.recommendations
    ai_profile.recommended_partner_type = result.recommended_partner_type
    ai_profile.source = result.source

    db.commit()
    db.refresh(ai_profile)
    return AIProfilePublic.model_validate(ai_profile)


@router.get("/personality", response_model=AIProfilePublic)
def get_personality(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AIProfilePublic:
    ai_profile = db.scalar(select(AIProfile).where(AIProfile.user_id == current_user.id))
    if ai_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No personality yet. Generate one with POST /ai/personality.",
        )
    return AIProfilePublic.model_validate(ai_profile)
