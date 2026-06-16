"""
Profile endpoints (spec §2).

  POST /profiles      -> create the caller's profile (409 if it exists)
  PUT  /profiles      -> replace the caller's profile fields
  GET  /profiles/me   -> the caller's profile

`extract_goal_tags` runs on every create and update, so `goal_tags` always
reflects the current goal/subjects and matching never touches the AI layer.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.profile import ProfileInput, ProfilePublic
from app.services.goal_tags import extract_goal_tags

router = APIRouter(prefix="/profiles", tags=["profiles"])


def _get_profile(db: Session, user_id) -> StudentProfile | None:
    return db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))


def _apply(profile: StudentProfile, data: ProfileInput) -> None:
    profile.course = data.course
    profile.year = data.year
    profile.subjects = data.subjects
    profile.learning_style = data.learning_style.value
    profile.preferred_study_time = data.preferred_study_time.value
    profile.study_environment = data.study_environment.value
    profile.study_intensity = data.study_intensity.value
    profile.current_goal = data.current_goal
    profile.daily_goal_hours = data.daily_goal_hours
    profile.motivation_type = data.motivation_type.value if data.motivation_type else None
    profile.experience_level = data.experience_level.value if data.experience_level else None
    # Deterministic, AI-independent. Recomputed every write.
    profile.goal_tags = extract_goal_tags(data.current_goal, data.subjects)


@router.post("", response_model=ProfilePublic, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: ProfileInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfilePublic:
    if _get_profile(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists. Use PUT /profiles to update it.",
        )
    profile = StudentProfile(user_id=current_user.id)
    _apply(profile, payload)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return ProfilePublic.model_validate(profile)


@router.put("", response_model=ProfilePublic)
def update_profile(
    payload: ProfileInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfilePublic:
    profile = _get_profile(db, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile yet. Use POST /profiles to create one.",
        )
    _apply(profile, payload)
    db.commit()
    db.refresh(profile)
    return ProfilePublic.model_validate(profile)


@router.get("/me", response_model=ProfilePublic)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfilePublic:
    profile = _get_profile(db, current_user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile yet.")
    return ProfilePublic.model_validate(profile)
