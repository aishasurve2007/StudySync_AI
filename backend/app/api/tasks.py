"""
Task endpoints (spec §6).

  POST /tasks/plan        -> AI generates a study plan (deterministic fallback)
  POST /tasks             -> create a single task manually
  GET  /tasks             -> list the caller's tasks
  POST /tasks/{id}/complete -> mark complete

Every creation emits TASK_CREATED and every completion emits TASK_COMPLETED,
written in the SAME transaction as the task row (see services/events.py).
"""
from datetime import datetime, timedelta, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.enums import EventType, TaskStatus
from app.models.student_profile import StudentProfile
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskPlanRequest, TaskPlanResponse, TaskPublic
from app.services.ai.base import AIProvider
from app.services.ai.factory import get_ai_provider
from app.services.events import log_event
from app.services.gamification import recompute_rewards
from app.services.task_planner import plan_tasks

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/plan", response_model=TaskPlanResponse, status_code=status.HTTP_201_CREATED)
def plan(
    payload: TaskPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    provider: AIProvider = Depends(get_ai_provider),
) -> TaskPlanResponse:
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    goal_tags = profile.goal_tags if profile else []

    planned, source = plan_tasks(payload.goal, payload.deadline_days, goal_tags, provider)
    deadline = datetime.now(timezone.utc) + timedelta(days=payload.deadline_days)

    created: list[Task] = []
    for pt in planned:
        task = Task(
            user_id=current_user.id, title=pt.title, priority=pt.priority,
            estimated_time=pt.estimated_time, deadline=deadline, status=TaskStatus.PENDING.value,
        )
        db.add(task)
        db.flush()  # assign task.id before emitting the event
        log_event(db, current_user.id, EventType.TASK_CREATED, {"task_id": str(task.id)})
        created.append(task)

    db.commit()
    for t in created:
        db.refresh(t)
    return TaskPlanResponse(source=source, tasks=[TaskPublic.model_validate(t) for t in created])


@router.post("", response_model=TaskPublic, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskPublic:
    task = Task(
        user_id=current_user.id, title=payload.title, description=payload.description,
        priority=payload.priority.value, estimated_time=payload.estimated_time,
        deadline=payload.deadline, status=TaskStatus.PENDING.value,
    )
    db.add(task)
    db.flush()
    log_event(db, current_user.id, EventType.TASK_CREATED, {"task_id": str(task.id)})
    db.commit()
    db.refresh(task)
    return TaskPublic.model_validate(task)


@router.get("", response_model=list[TaskPublic])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskPublic]:
    tasks = db.scalars(
        select(Task).where(Task.user_id == current_user.id).order_by(Task.created_at.desc())
    ).all()
    return [TaskPublic.model_validate(t) for t in tasks]


@router.post("/{task_id}/complete", response_model=TaskPublic)
def complete_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskPublic:
    task = db.scalar(
        select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    if task.status == TaskStatus.COMPLETED.value:
        return TaskPublic.model_validate(task)  # idempotent

    task.status = TaskStatus.COMPLETED.value
    task.completed_at = datetime.now(timezone.utc)
    # domain write + event + XP recompute, all in one transaction
    log_event(db, current_user.id, EventType.TASK_COMPLETED, {"task_id": str(task.id)})
    recompute_rewards(db, current_user)
    db.commit()
    db.refresh(task)
    return TaskPublic.model_validate(task)
