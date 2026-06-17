"""Study room tests (spec §5): REST lifecycle + presence store + socket app."""
import asyncio
import uuid

from app.services.presence import InMemoryPresenceStore


# ---------- in-memory presence store (unit) ----------

def test_presence_add_status_remove():
    store = InMemoryPresenceStore()

    async def run():
        await store.add("room1", "u1", "Aisha", "online")
        await store.add("room1", "u2", "Priya", "online")
        members = await store.members("room1")
        assert len(members) == 2

        await store.set_status("room1", "u1", "focusing")
        m = {x["user_id"]: x for x in await store.members("room1")}
        assert m["u1"]["status"] == "focusing"

        await store.remove("room1", "u1")
        assert len(await store.members("room1")) == 1

        await store.remove("room1", "u2")
        assert await store.members("room1") == []   # room cleaned up when empty

    asyncio.run(run())


# ---------- socket app wiring (import-level) ----------

def test_socket_app_builds():
    # Importing main must construct the combined Socket.IO ASGI app without error.
    from app.main import socket_app, sio
    assert socket_app is not None
    assert sio is not None


# ---------- rooms REST ----------

def _register(client, email, name) -> str:
    r = client.post("/auth/register", json={"email": email, "password": "supersecret1", "name": name})
    assert r.status_code == 201
    return r.json()["access_token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_room_auto_joins_creator(auth_client):
    r = auth_client.post("/rooms", json={"subject": "Machine Learning", "max_users": 4})
    assert r.status_code == 201
    body = r.json()
    assert body["subject"] == "Machine Learning"
    assert body["member_count"] == 1            # creator auto-joined
    assert len(body["members"]) == 1


def test_list_rooms(auth_client):
    auth_client.post("/rooms", json={"subject": "Stats"})
    rooms = auth_client.get("/rooms").json()
    assert len(rooms) == 1
    assert rooms[0]["subject"] == "Stats"


def test_join_room_and_member_count(client):
    a = _register(client, "a@x.com", "A")
    b = _register(client, "b@x.com", "B")
    room = client.post("/rooms", json={"subject": "DSA"}, headers=_h(a)).json()
    rid = room["id"]

    r = client.post(f"/rooms/{rid}/join", headers=_h(b))
    assert r.status_code == 200
    assert r.json()["member_count"] == 2


def test_join_is_idempotent(client):
    a = _register(client, "a@x.com", "A")
    room = client.post("/rooms", json={"subject": "DSA"}, headers=_h(a)).json()
    # creator joins again -> still 1 member, no error
    r = client.post(f"/rooms/{room['id']}/join", headers=_h(a))
    assert r.status_code == 200 and r.json()["member_count"] == 1


def test_room_full_rejected(client):
    a = _register(client, "a@x.com", "A")
    b = _register(client, "b@x.com", "B")
    c = _register(client, "c@x.com", "C")
    room = client.post("/rooms", json={"subject": "DSA", "max_users": 2}, headers=_h(a)).json()
    rid = room["id"]
    assert client.post(f"/rooms/{rid}/join", headers=_h(b)).status_code == 200   # 2/2
    assert client.post(f"/rooms/{rid}/join", headers=_h(c)).status_code == 409    # full


def test_leave_room_closes_when_empty(client):
    a = _register(client, "a@x.com", "A")
    room = client.post("/rooms", json={"subject": "DSA"}, headers=_h(a)).json()
    rid = room["id"]
    assert client.post(f"/rooms/{rid}/leave", headers=_h(a)).status_code == 200
    # room is now closed -> not listed
    assert client.get("/rooms", headers=_h(a)).json() == []


def test_join_missing_room_404(auth_client):
    assert auth_client.post(f"/rooms/{uuid.uuid4()}/join").status_code == 404


def test_rooms_require_auth(client):
    assert client.get("/rooms").status_code == 401
