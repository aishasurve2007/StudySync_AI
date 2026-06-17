"""
Presence store — the EPHEMERAL side of rooms (spec §5).

Tracks who is connected to a room right now and their live status
(ONLINE/FOCUSING/BREAK). Two interchangeable implementations:

- InMemoryPresenceStore : a process-local dict. Perfect for a single-instance
  demo; presence is lost on restart (which is correct — it's ephemeral).
- RedisPresenceStore     : a Redis hash per room, so presence is shared across
  multiple server instances (needed once you scale horizontally).

Chosen by REDIS_URL in config — exactly like the AI provider swap. The socket
layer depends only on this interface, never on Redis directly.
"""
import json
from typing import Protocol

from app.core.config import settings


class PresenceStore(Protocol):
    async def add(self, room_id: str, user_id: str, name: str, status: str) -> None: ...
    async def set_status(self, room_id: str, user_id: str, status: str) -> None: ...
    async def remove(self, room_id: str, user_id: str) -> None: ...
    async def members(self, room_id: str) -> list[dict]: ...


class InMemoryPresenceStore:
    def __init__(self) -> None:
        self._rooms: dict[str, dict[str, dict]] = {}

    async def add(self, room_id, user_id, name, status) -> None:
        self._rooms.setdefault(room_id, {})[user_id] = {
            "user_id": user_id, "name": name, "status": status
        }

    async def set_status(self, room_id, user_id, status) -> None:
        if room_id in self._rooms and user_id in self._rooms[room_id]:
            self._rooms[room_id][user_id]["status"] = status

    async def remove(self, room_id, user_id) -> None:
        if room_id in self._rooms:
            self._rooms[room_id].pop(user_id, None)
            if not self._rooms[room_id]:
                del self._rooms[room_id]

    async def members(self, room_id) -> list[dict]:
        return list(self._rooms.get(room_id, {}).values())


class RedisPresenceStore:
    def __init__(self, url: str) -> None:
        import redis.asyncio as aioredis
        self._r = aioredis.from_url(url, decode_responses=True)

    def _key(self, room_id: str) -> str:
        return f"presence:{room_id}"

    async def add(self, room_id, user_id, name, status) -> None:
        await self._r.hset(self._key(room_id), user_id,
                           json.dumps({"user_id": user_id, "name": name, "status": status}))

    async def set_status(self, room_id, user_id, status) -> None:
        raw = await self._r.hget(self._key(room_id), user_id)
        if raw:
            data = json.loads(raw)
            data["status"] = status
            await self._r.hset(self._key(room_id), user_id, json.dumps(data))

    async def remove(self, room_id, user_id) -> None:
        await self._r.hdel(self._key(room_id), user_id)

    async def members(self, room_id) -> list[dict]:
        raw = await self._r.hgetall(self._key(room_id))
        return [json.loads(v) for v in raw.values()]


_store: PresenceStore | None = None


def get_presence_store() -> PresenceStore:
    global _store
    if _store is None:
        _store = RedisPresenceStore(settings.REDIS_URL) if settings.REDIS_URL else InMemoryPresenceStore()
    return _store
