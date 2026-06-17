"""
Real-time layer (spec §5): Socket.IO presence + live status.

Flow:
  - On connect, the client sends its JWT in the `auth` payload. We decode it;
    a bad/absent token rejects the connection.
  - `join_room {room_id}`  : verifies durable membership (room_members), enters
    the Socket.IO room, marks the user ONLINE in the presence store, and
    broadcasts the updated presence list.
  - `set_status {room_id, status}` : updates ONLINE/FOCUSING/BREAK and rebroadcasts.
  - `leave_room` / disconnect : removes presence and rebroadcasts.

Scaling: if REDIS_URL is set, Socket.IO uses a Redis manager so broadcasts
reach clients connected to other server instances; otherwise it runs single
instance in memory. Either way the API behaves the same.
"""
import socketio

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.enums import PresenceStatus
from app.models.study_room import RoomMember
from app.models.user import User
from app.services.presence import get_presence_store

_client_manager = socketio.AsyncRedisManager(settings.REDIS_URL) if settings.REDIS_URL else None

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.cors_origins_list,
    client_manager=_client_manager,
)

_presence = get_presence_store()


def _is_member(user_id: str, room_id: str) -> tuple[bool, str | None]:
    """Check durable membership and fetch the display name (sync DB, short-lived session)."""
    from sqlalchemy import select
    import uuid as _uuid
    db = SessionLocal()
    try:
        member = db.scalar(
            select(RoomMember).where(
                RoomMember.room_id == _uuid.UUID(room_id),
                RoomMember.user_id == _uuid.UUID(user_id),
            )
        )
        if member is None:
            return False, None
        user = db.get(User, _uuid.UUID(user_id))
        return True, (user.name if user else "Unknown")
    except (ValueError, Exception):
        return False, None
    finally:
        db.close()


async def _broadcast_presence(room_id: str) -> None:
    await sio.emit("presence", {"room_id": room_id, "members": await _presence.members(room_id)}, room=room_id)


@sio.event
async def connect(sid, environ, auth):
    token = (auth or {}).get("token")
    user_id = decode_access_token(token) if token else None
    if not user_id:
        return False  # reject the connection
    await sio.save_session(sid, {"user_id": user_id, "rooms": set()})


@sio.on("join_room")
async def join_room(sid, data):
    room_id = str((data or {}).get("room_id", ""))
    session = await sio.get_session(sid)
    ok, name = _is_member(session["user_id"], room_id)
    if not ok:
        await sio.emit("error", {"detail": "Not a member of this room."}, to=sid)
        return
    await sio.enter_room(sid, room_id)
    session["rooms"].add(room_id)
    await sio.save_session(sid, session)
    await _presence.add(room_id, session["user_id"], name, PresenceStatus.ONLINE.value)
    await _broadcast_presence(room_id)


@sio.on("set_status")
async def set_status(sid, data):
    room_id = str((data or {}).get("room_id", ""))
    new_status = (data or {}).get("status")
    if new_status not in (s.value for s in PresenceStatus):
        await sio.emit("error", {"detail": "Invalid status."}, to=sid)
        return
    session = await sio.get_session(sid)
    await _presence.set_status(room_id, session["user_id"], new_status)
    await _broadcast_presence(room_id)


@sio.on("leave_room")
async def leave_room(sid, data):
    room_id = str((data or {}).get("room_id", ""))
    session = await sio.get_session(sid)
    await sio.leave_room(sid, room_id)
    session["rooms"].discard(room_id)
    await sio.save_session(sid, session)
    await _presence.remove(room_id, session["user_id"])
    await _broadcast_presence(room_id)


@sio.event
async def disconnect(sid):
    try:
        session = await sio.get_session(sid)
    except KeyError:
        return
    for room_id in list(session.get("rooms", [])):
        await _presence.remove(room_id, session["user_id"])
        await _broadcast_presence(room_id)
