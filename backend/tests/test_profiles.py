"""Profile endpoint tests (spec §2)."""
from tests.conftest import VALID_PROFILE


def test_get_profile_404_before_create(auth_client):
    assert auth_client.get("/profiles/me").status_code == 404


def test_create_profile_derives_goal_tags(auth_client):
    r = auth_client.post("/profiles", json=VALID_PROFILE)
    assert r.status_code == 201
    # tags derived from "Prepare ML interview" + subjects, by the backend
    assert r.json()["goal_tags"] == ["interview", "machine learning", "statistics"]


def test_duplicate_profile_rejected(auth_client):
    assert auth_client.post("/profiles", json=VALID_PROFILE).status_code == 201
    assert auth_client.post("/profiles", json=VALID_PROFILE).status_code == 409


def test_invalid_enum_rejected(auth_client):
    bad = dict(VALID_PROFILE, learning_style="telepathy")
    assert auth_client.post("/profiles", json=bad).status_code == 422


def test_update_recomputes_goal_tags(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    updated = dict(VALID_PROFILE, current_goal="Build a full stack web development project", subjects=[])
    r = auth_client.put("/profiles", json=updated)
    assert r.status_code == 200
    assert r.json()["goal_tags"] == ["project", "web development"]


def test_client_cannot_set_goal_tags(auth_client):
    # Even if the client sends goal_tags, the backend ignores them.
    sneaky = dict(VALID_PROFILE, goal_tags=["hacked"])
    r = auth_client.post("/profiles", json=sneaky)
    assert r.status_code == 201
    assert "hacked" not in r.json()["goal_tags"]


def test_update_before_create_404(auth_client):
    assert auth_client.put("/profiles", json=VALID_PROFILE).status_code == 404


def test_profile_requires_auth(client):
    assert client.get("/profiles/me").status_code == 401
    assert client.post("/profiles", json=VALID_PROFILE).status_code == 401
