"""
Personality engine tests (spec §3).

These lock down the grounding guarantee: traits trace to answers, the AI
cannot inject ungrounded traits, and the deterministic fallback works with
no provider.
"""
import pytest

from app.models.student_profile import StudentProfile
from app.services.ai.factory import get_ai_provider
from app.services.ai.providers import NullProvider
from app.services.personality import generate_personality
from tests.conftest import VALID_PROFILE


def _profile(**overrides) -> StudentProfile:
    data = {
        "course": "CS", "year": 2, "subjects": ["Machine Learning"],
        "learning_style": "practice", "preferred_study_time": "night",
        "study_environment": "quiet", "study_intensity": "casual",
        "current_goal": "Prepare ML interview", "goal_tags": ["machine learning", "interview"],
        "daily_goal_hours": 2.0, "motivation_type": "achievement",
        "experience_level": "beginner",
    }
    data.update(overrides)
    return StudentProfile(**data)


# ---- deterministic grounding (NullProvider => fallback) ----

def test_night_owl_casual_yields_distraction_weakness():
    res = generate_personality(_profile(), NullProvider())
    assert res.source == "fallback"
    assert any("distraction" in w.lower() for w in res.weaknesses)


def test_no_distraction_weakness_when_intensive():
    # Same night-time, but intensive -> the night weakness must NOT appear.
    res = generate_personality(_profile(study_intensity="intensive"), NullProvider())
    assert not any("distraction" in w.lower() for w in res.weaknesses)


def test_collaborative_strength_grounded_in_group_style():
    res = generate_personality(
        _profile(learning_style="group", study_environment="discussion"), NullProvider()
    )
    assert any("collaborativ" in s.lower() for s in res.strengths)


def test_goal_oriented_strength_present_when_goal_set():
    res = generate_personality(_profile(), NullProvider())
    assert any("goal" in s.lower() for s in res.strengths)


def test_sparse_profile_returns_fewer_traits_not_invented():
    # Minimal profile: regular intensity, no goal -> few/zero strengths,
    # and definitely no invented ones.
    res = generate_personality(
        _profile(current_goal=None, goal_tags=[], study_intensity="regular",
                 learning_style="reading", study_environment="quiet",
                 experience_level="intermediate", daily_goal_hours=2.0,
                 motivation_type="growth", preferred_study_time="morning"),
        NullProvider(),
    )
    assert len(res.strengths) <= 4
    assert isinstance(res.personality_type, str) and res.personality_type


# ---- AI layer is constrained to the menu ----

class FakeAIProvider:
    """Returns a valid selection plus an INVALID/hallucinated id."""
    name = "fake"

    def complete_json(self, system, user):
        return {
            "personality_type": "Focused Night Strategist",
            "strength_ids": ["S_GOAL", "S_NONEXISTENT"],   # second is a hallucination
            "weakness_ids": ["W_NIGHT", "W_FAKE"],          # second is a hallucination
            "labels": {"S_GOAL": "Driven by a clear goal"},
        }


def test_ai_hallucinated_traits_are_dropped():
    res = generate_personality(_profile(), FakeAIProvider())
    assert res.source == "ai"
    assert res.personality_type == "Focused Night Strategist"
    # the relabelled grounded trait survives
    assert "Driven by a clear goal" in res.strengths
    # nothing ungrounded leaks through (we never even have labels for fake ids)
    joined = " ".join(res.strengths + res.weaknesses).lower()
    assert "nonexistent" not in joined and "fake" not in joined


class BrokenAIProvider:
    name = "broken"

    def complete_json(self, system, user):
        return "this is not a dict"  # malformed


def test_malformed_ai_response_falls_back():
    res = generate_personality(_profile(), BrokenAIProvider())
    assert res.source == "fallback"
    assert res.personality_type  # still produces a grounded result


# ---- API endpoint ----

def test_generate_requires_profile(auth_client):
    assert auth_client.post("/ai/personality").status_code == 404


def test_generate_and_fetch_personality(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    r = auth_client.post("/ai/personality")
    assert r.status_code == 201
    body = r.json()
    assert body["personality_type"]
    assert body["source"] in ("ai", "fallback")
    # default test env has no API key -> deterministic fallback
    assert body["source"] == "fallback"

    got = auth_client.get("/ai/personality")
    assert got.status_code == 200
    assert got.json()["personality_type"] == body["personality_type"]


def test_regenerate_overwrites(auth_client):
    auth_client.post("/profiles", json=VALID_PROFILE)
    auth_client.post("/ai/personality")
    # second call should not 409 — it upserts
    assert auth_client.post("/ai/personality").status_code == 201


def test_personality_requires_auth(client):
    assert client.get("/ai/personality").status_code == 401
