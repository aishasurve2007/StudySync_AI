"""Tests for tasks, focus sessions, productivity (spec §6–8)."""
from tests.conftest import VALID_PROFILE


# ---------- tasks ----------

def test_plan_generates_tasks_and_events(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    r = auth_client.post("/tasks/plan", json={"goal": "Prepare ML interview", "deadline_days": 14})
    assert r.status_code == 201
    body = r.json()
    assert body["source"] == "fallback"           # no API key in tests
    assert len(body["tasks"]) >= 3
    # each task got persisted and listed
    listed = auth_client.get("/tasks").json()
    assert len(listed) == len(body["tasks"])


def test_short_deadline_makes_fewer_tasks(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    r = auth_client.post("/tasks/plan", json={"goal": "Quick revision", "deadline_days": 2})
    assert len(r.json()["tasks"]) == 3


def test_create_and_complete_task(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    t = auth_client.post("/tasks", json={"title": "Read chapter 3"}).json()
    assert t["status"] == "pending" and t["completed_at"] is None

    done = auth_client.post(f"/tasks/{t['id']}/complete").json()
    assert done["status"] == "completed"
    assert done["completed_at"] is not None


def test_complete_task_is_idempotent(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    t = auth_client.post("/tasks", json={"title": "x"}).json()
    auth_client.post(f"/tasks/{t['id']}/complete")
    # second completion must not error or double-count
    r = auth_client.post(f"/tasks/{t['id']}/complete")
    assert r.status_code == 200


def test_complete_missing_task_404(auth_client):
    import uuid
    assert auth_client.post(f"/tasks/{uuid.uuid4()}/complete").status_code == 404


# ---------- focus ----------

def test_pomodoro_full_session_counts(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    s = auth_client.post("/focus/start", json={"mode": "pomodoro", "duration": 25}).json()
    done = auth_client.post(f"/focus/{s['id']}/complete", json={"actual_minutes": 25}).json()
    assert done["completed"] is True
    assert done["actual_minutes"] == 25


def test_actual_minutes_capped_to_planned(auth_client):
    # Anti-abuse: claim 999 minutes on a 25-min pomodoro -> credited 25.
    auth_client.post("/profiles", json=VALID_PROFILE)
    s = auth_client.post("/focus/start", json={"mode": "pomodoro", "duration": 25}).json()
    done = auth_client.post(f"/focus/{s['id']}/complete", json={"actual_minutes": 999}).json()
    assert done["actual_minutes"] == 25


def test_unfinished_session_not_completed(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    s = auth_client.post("/focus/start", json={"mode": "deep_work", "duration": 50}).json()
    done = auth_client.post(f"/focus/{s['id']}/complete", json={"actual_minutes": 10}).json()
    assert done["completed"] is False   # didn't run full -> won't count toward score


def test_stopwatch_session(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    s = auth_client.post("/focus/start", json={"mode": "stopwatch", "duration": 0}).json()
    done = auth_client.post(f"/focus/{s['id']}/complete", json={"actual_minutes": 40}).json()
    assert done["completed"] is True and done["actual_minutes"] == 40


# ---------- productivity score (reads activity_logs) ----------

def test_productivity_score_reflects_activity(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)  # daily_goal_hours = 3
    # 2 tasks created, 1 completed
    t1 = auth_client.post("/tasks", json={"title": "a"}).json()
    auth_client.post("/tasks", json={"title": "b"})
    auth_client.post(f"/tasks/{t1['id']}/complete")
    # one 30-min completed session
    s = auth_client.post("/focus/start", json={"mode": "deep_work", "duration": 30}).json()
    auth_client.post(f"/focus/{s['id']}/complete", json={"actual_minutes": 30})

    score = auth_client.get("/productivity/score").json()
    assert score["created_tasks"] == 2
    assert score["completed_tasks"] == 1
    assert score["task_completion"] == 0.5
    assert score["total_focus_minutes"] == 30
    assert score["active_days"] == 1            # all today, user's tz
    # 0.5*40 + (30/(3*60*7))*40 + (1/7)*20  ≈ 20 + 0.95 + 2.86 = 23.8 -> 24
    assert score["score"] == 24


def test_unfinished_session_excluded_from_focus_minutes(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    s = auth_client.post("/focus/start", json={"mode": "deep_work", "duration": 50}).json()
    auth_client.post(f"/focus/{s['id']}/complete", json={"actual_minutes": 10})  # not completed
    score = auth_client.get("/productivity/score").json()
    assert score["total_focus_minutes"] == 0


def test_empty_productivity_score_is_zero(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    score = auth_client.get("/productivity/score").json()
    assert score["score"] == 0
    assert score["active_days"] == 0


# ---------- auth ----------

def test_chunk5_requires_auth(client):
    assert client.get("/tasks").status_code == 401
    assert client.get("/focus/sessions").status_code == 401
    assert client.get("/productivity/score").status_code == 401
