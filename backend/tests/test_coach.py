"""AI Study Coach tests (spec §11)."""
from app.services.coach import _fallback_insight, generate_insight
from tests.conftest import VALID_PROFILE


def test_cold_start_insight():
    ctx = {"completed_tasks": 0, "started_sessions": 0, "completed_sessions": 0,
           "missed_sessions": 0, "best_time_of_day": None, "best_time_count": 0,
           "active_days": 0, "study_minutes": 0, "created_tasks": 0, "window_days": 7}
    assert "start" in _fallback_insight(ctx).lower()


def test_unfinished_sessions_insight():
    ctx = {"completed_tasks": 0, "started_sessions": 3, "completed_sessions": 0,
           "missed_sessions": 3, "best_time_of_day": None, "best_time_count": 0,
           "active_days": 0, "study_minutes": 0, "created_tasks": 0, "window_days": 7}
    assert "finish" in _fallback_insight(ctx).lower() or "complete" in _fallback_insight(ctx).lower()


def test_best_time_insight_is_grounded():
    ctx = {"completed_tasks": 2, "started_sessions": 3, "completed_sessions": 3,
           "missed_sessions": 0, "best_time_of_day": "evening", "best_time_count": 3,
           "active_days": 2, "study_minutes": 120, "created_tasks": 2, "window_days": 7}
    assert "evening" in _fallback_insight(ctx)


class FakeAI:
    name = "fake"
    def complete_json(self, system, user):
        return {"insight": "You focus best in the evening — block 7pm for hard topics."}


def test_ai_insight_used_when_available():
    ctx = {"completed_tasks": 1, "started_sessions": 1, "completed_sessions": 1,
           "missed_sessions": 0, "best_time_of_day": "evening", "best_time_count": 1,
           "active_days": 1, "study_minutes": 30, "created_tasks": 1, "window_days": 7}
    text, source = generate_insight(ctx, FakeAI())
    assert source == "ai" and "evening" in text


class BrokenAI:
    name = "broken"
    def complete_json(self, system, user):
        return None


def test_falls_back_when_ai_unavailable():
    ctx = {"completed_tasks": 1, "started_sessions": 0, "completed_sessions": 0,
           "missed_sessions": 0, "best_time_of_day": None, "best_time_count": 0,
           "active_days": 1, "study_minutes": 0, "created_tasks": 1, "window_days": 7}
    _, source = generate_insight(ctx, BrokenAI())
    assert source == "fallback"


# ---- API + real activity ----

def test_coach_endpoint_reflects_activity(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    # complete a task and a full session
    t = auth_client.post("/tasks", json={"title": "x"}).json()
    auth_client.post(f"/tasks/{t['id']}/complete")
    s = auth_client.post("/focus/start", json={"mode": "deep_work", "duration": 30}).json()
    auth_client.post(f"/focus/{s['id']}/complete", json={"actual_minutes": 30})

    r = auth_client.get("/coach/insight")
    assert r.status_code == 200
    body = r.json()
    assert body["insight"]
    assert body["source"] == "fallback"          # no API key in tests
    assert body["context"]["completed_tasks"] == 1
    assert body["context"]["completed_sessions"] == 1
    assert body["context"]["study_minutes"] == 30


def test_coach_missed_session_counts(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    s = auth_client.post("/focus/start", json={"mode": "deep_work", "duration": 50}).json()
    auth_client.post(f"/focus/{s['id']}/complete", json={"actual_minutes": 10})  # unfinished
    ctx = auth_client.get("/coach/insight").json()["context"]
    assert ctx["started_sessions"] == 1
    assert ctx["completed_sessions"] == 0
    assert ctx["missed_sessions"] == 1


def test_coach_requires_auth(client):
    assert client.get("/coach/insight").status_code == 401
