"""
Focus session endpoints (spec §7) + anti-abuse (§8).

  POST /focus/start          -> begin a session (emits SESSION_STARTED)
  POST /focus/{id}/complete  -> finish it (emits SESSION_COMPLETED iff completed)
  GET  /focus/sessions       -> list the caller's sessions

Anti-abuse: credited `actual_minutes` is capped to the planned duration for
timed modes, so a 25-minute Pomodoro can't be reported as 999 minutes. A timed
session only counts as `completed` (and only then emits SESSION_COMPLETED) if it
ran the full planned duration — so unfinished sessions never inflate the score.
"""
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.enums import EventType, FocusMode
from app.models.focus_session import FocusSession
from app.models.task import Task
from app.models.user import User
from app.schemas.focus import FocusCompleteRequest, FocusSessionPublic, FocusStartRequest
from app.services.events import log_event
from app.services.gamification import recompute_rewards

router = APIRouter(prefix="/focus", tags=["focus"])

_MAX_STOPWATCH = 1440  # 24h hard cap


@router.post("/start", response_model=FocusSessionPublic, status_code=status.HTTP_201_CREATED)
def start_session(
    payload: FocusStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FocusSessionPublic:
    if payload.task_id is not None:
        owns = db.scalar(select(Task).where(Task.id == payload.task_id, Task.user_id == current_user.id))
        if owns is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    session = FocusSession(
        user_id=current_user.id, task_id=payload.task_id, mode=payload.mode.value,
        duration=payload.duration, actual_minutes=0, completed=False,
    )
    db.add(session)
    db.flush()
    log_event(db, current_user.id, EventType.SESSION_STARTED,
              {"session_id": str(session.id), "mode": session.mode})
    db.commit()
    db.refresh(session)
    return FocusSessionPublic.model_validate(session)


@router.post("/{session_id}/complete", response_model=FocusSessionPublic)
def complete_session(
    session_id: uuid.UUID,
    payload: FocusCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FocusSessionPublic:
    session = db.scalar(
        select(FocusSession).where(FocusSession.id == session_id, FocusSession.user_id == current_user.id)
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    if session.ended_at is not None:
        return FocusSessionPublic.model_validate(session)  # idempotent

    if session.mode == FocusMode.STOPWATCH.value:
        credited = min(payload.actual_minutes or 0, _MAX_STOPWATCH)
        completed = credited > 0
    else:
        planned = session.duration or 0
        reported = payload.actual_minutes if payload.actual_minutes is not None else planned
        credited = min(reported, planned) if planned > 0 else min(reported, _MAX_STOPWATCH)
        completed = planned > 0 and credited >= planned

    session.actual_minutes = credited
    session.completed = completed
    session.ended_at = datetime.now(timezone.utc)

    # Only completed sessions emit SESSION_COMPLETED -> only they count toward focus minutes.
    if completed:
        log_event(db, current_user.id, EventType.SESSION_COMPLETED,
                  {"session_id": str(session.id), "mode": session.mode, "actual_minutes": credited})
        recompute_rewards(db, current_user)
    db.commit()
    db.refresh(session)
    return FocusSessionPublic.model_validate(session)


@router.get("/sessions", response_model=list[FocusSessionPublic])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FocusSessionPublic]:
    sessions = db.scalars(
        select(FocusSession).where(FocusSession.user_id == current_user.id).order_by(FocusSession.started_at.desc())
    ).all()
    return [FocusSessionPublic.model_validate(s) for s in sessions]
