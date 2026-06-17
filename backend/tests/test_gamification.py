"""Tests for XP/garden, weekly report, dashboard (spec §9–10)."""
from app.services.gamification import level_and_stage
from tests.conftest import VALID_PROFILE


# ---- level / garden stage (pure function) ----

def test_garden_stage_thresholds():
    assert level_and_stage(0)[1] == "Seed"
    assert level_and_stage(99)[1] == "Seed"
    assert level_and_stage(100)[1] == "Sprout"
    assert level_and_stage(300)[1] == "Flower"
    assert level_and_stage(700)[1] == "Tree"
    assert level_and_stage(1500)[1] == "Fruit Tree"


def test_progress_to_next_stage():
    level, stage, next_stage, xp_to_next = level_and_stage(60)
    assert stage == "Seed" and next_stage == "Sprout" and xp_to_next == 40


# ---- XP from real activity ----

def _complete_task(client):
    t = client.post("/tasks", json={"title": "x"}).json()
    client.post(f"/tasks/{t['id']}/complete")


def _full_session(client, minutes=5):
    s = client.post("/focus/start", json={"mode": "pomodoro", "duration": minutes}).json()
    client.post(f"/focus/{s['id']}/complete", json={"actual_minutes": minutes})


def test_single_task_awards_xp_with_streak_bonus(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    _complete_task(auth_client)
    r = auth_client.get("/rewards").json()
    # 1 task (10) + daily streak bonus (50) = 60
    assert r["xp"] == 60
    assert r["garden_stage"] == "Seed"
    assert r["xp_to_next"] == 40


def test_task_and_session_same_day(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    _complete_task(auth_client)
    _full_session(auth_client)
    r = auth_client.get("/rewards").json()
    # 10 (task) + 20 (session) + 50 (streak) = 80
    assert r["xp"] == 80


def test_max_six_rewarded_sessions_per_day(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    for _ in range(7):           # 7 sessions, only 6 should be rewarded
        _full_session(auth_client)
    r = auth_client.get("/rewards").json()
    # min(7,6)*20 + 50 streak = 170  (NOT 7*20+50=190)
    assert r["xp"] == 170


def test_daily_xp_cap(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    for _ in range(16):          # 16 tasks -> 160 + 50 = 210, capped at 200
        _complete_task(auth_client)
    r = auth_client.get("/rewards").json()
    assert r["xp"] == 200


# ---- weekly report ----

def test_weekly_report(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    _complete_task(auth_client)
    s = auth_client.post("/focus/start", json={"mode": "deep_work", "duration": 30}).json()
    auth_client.post(f"/focus/{s['id']}/complete", json={"actual_minutes": 30})

    w = auth_client.get("/analytics/weekly").json()
    assert w["tasks_completed"] == 1
    assert w["focus_sessions"] == 1
    assert w["study_minutes"] == 30
    assert w["current_streak"] == 1
    assert w["active_days"] == 1
    assert w["consistency_pct"] == 14   # 1/7 -> 14%


# ---- dashboard ----

def test_dashboard_composes_everything(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    auth_client.post("/ai/personality")
    _complete_task(auth_client)

    d = auth_client.get("/dashboard").json()
    assert d["has_profile"] is True
    assert d["personality_type"]               # generated above
    assert d["rewards"]["xp"] == 60
    assert d["productivity"]["completed_tasks"] == 1
    assert d["weekly"]["tasks_completed"] == 1


# ---- auth ----

def test_chunk6_requires_auth(client):
    assert client.get("/rewards").status_code == 401
    assert client.get("/analytics/weekly").status_code == 401
    assert client.get("/dashboard").status_code == 401
