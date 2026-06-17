"""
Study room REST endpoints (spec §5) — durable lifecycle/membership.

  POST /rooms            -> create a room (creator auto-joins)
  GET  /rooms            -> list active rooms (+ member counts)
  GET  /rooms/{id}       -> room detail + members
  POST /rooms/{id}/join  -> join (checks open + not full); emits ROOM_JOINED
  POST /rooms/{id}/leave -> leave (closes the room if it becomes empty)

Live presence/status comes over Socket.IO (see app/realtime/socket.py); this
layer only manages who belongs to a room.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.enums import EventType, RoomStatus
from app.models.study_room import RoomMember, StudyRoom
from app.models.user import User
from app.schemas.room import RoomCreate, RoomDetail, RoomMemberOut, RoomSummary
from app.services.events import log_event

router = APIRouter(prefix="/rooms", tags=["rooms"])


def _member_count(db: Session, room_id) -> int:
    return db.scalar(select(func.count()).select_from(RoomMember).where(RoomMember.room_id == room_id)) or 0


def _summary(db: Session, room: StudyRoom) -> RoomSummary:
    return RoomSummary(
        id=room.id, subject=room.subject, max_users=room.max_users, status=room.status,
        created_by=room.created_by, created_at=room.created_at,
        member_count=_member_count(db, room.id),
    )


@router.post("", response_model=RoomDetail, status_code=status.HTTP_201_CREATED)
def create_room(
    payload: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomDetail:
    room = StudyRoom(
        created_by=current_user.id, subject=payload.subject,
        max_users=payload.max_users, status=RoomStatus.ACTIVE.value,
    )
    db.add(room)
    db.flush()
    db.add(RoomMember(room_id=room.id, user_id=current_user.id))  # creator joins
    log_event(db, current_user.id, EventType.ROOM_JOINED, {"room_id": str(room.id)})
    db.commit()
    db.refresh(room)
    return _detail(db, room)


@router.get("", response_model=list[RoomSummary])
def list_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RoomSummary]:
    rooms = db.scalars(
        select(StudyRoom).where(StudyRoom.status == RoomStatus.ACTIVE.value).order_by(StudyRoom.created_at.desc())
    ).all()
    return [_summary(db, r) for r in rooms]


def _detail(db: Session, room: StudyRoom) -> RoomDetail:
    rows = db.execute(
        select(RoomMember, User).join(User, User.id == RoomMember.user_id)
        .where(RoomMember.room_id == room.id).order_by(RoomMember.joined_at)
    ).all()
    members = [RoomMemberOut(user_id=u.id, name=u.name, joined_at=m.joined_at) for m, u in rows]
    s = _summary(db, room)
    return RoomDetail(**s.model_dump(), members=members)


@router.get("/{room_id}", response_model=RoomDetail)
def get_room(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomDetail:
    room = db.get(StudyRoom, room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found.")
    return _detail(db, room)


@router.post("/{room_id}/join", response_model=RoomDetail)
def join_room(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomDetail:
    room = db.get(StudyRoom, room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found.")
    if room.status != RoomStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Room is closed.")

    already = db.scalar(
        select(RoomMember).where(RoomMember.room_id == room_id, RoomMember.user_id == current_user.id)
    )
    if already:
        return _detail(db, room)  # idempotent

    if _member_count(db, room_id) >= room.max_users:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Room is full.")

    db.add(RoomMember(room_id=room_id, user_id=current_user.id))
    log_event(db, current_user.id, EventType.ROOM_JOINED, {"room_id": str(room_id)})
    db.commit()
    db.refresh(room)
    return _detail(db, room)


@router.post("/{room_id}/leave", status_code=status.HTTP_200_OK)
def leave_room(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    member = db.scalar(
        select(RoomMember).where(RoomMember.room_id == room_id, RoomMember.user_id == current_user.id)
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not in this room.")
    db.delete(member)
    db.flush()
    # Close the room if it's now empty.
    if _member_count(db, room_id) == 0:
        room = db.get(StudyRoom, room_id)
        if room:
            room.status = RoomStatus.CLOSED.value
    db.commit()
    return {"left": True, "room_id": str(room_id)}
