"""Matching engine tests (spec §4)."""
from app.models.student_profile import StudentProfile
from app.services.matching import (
    _intensity_match,
    _jaccard,
    _schedule_match,
    compute_compatibility,
)


def _prof(**kw) -> StudentProfile:
    data = {
        "course": "CS", "subjects": ["Machine Learning", "Statistics"],
        "learning_style": "practice", "preferred_study_time": "evening",
        "study_environment": "quiet", "study_intensity": "intensive",
        "goal_tags": ["machine learning", "interview"], "daily_goal_hours": 3.0,
    }
    data.update(kw)
    return StudentProfile(**data)


# ---- component math ----

def test_jaccard():
    val, shared = _jaccard(["a", "b"], ["b", "c"])
    assert val == 1 / 3 and shared == {"b"}
    assert _jaccard([], [])[0] == 0.0


def test_schedule_exact_adjacent_far():
    assert _schedule_match("evening", "evening") == 1.0
    assert _schedule_match("afternoon", "evening") == 0.5   # adjacent
    assert _schedule_match("morning", "night") == 0.0       # far


def test_intensity_ordinal():
    assert _intensity_match("casual", "casual") == 1.0
    assert _intensity_match("casual", "regular") == 0.5
    assert _intensity_match("casual", "intensive") == 0.0


# ---- full score ----

def test_identical_profiles_score_100():
    me = _prof()
    assert compute_compatibility(me, _prof()).score == 100


def test_hand_computed_score_60():
    me = _prof()
    other = _prof(
        preferred_study_time="afternoon",      # adjacent -> 0.5 * 30
        subjects=["Machine Learning"],          # jaccard 0.5 * 25
        learning_style="practice",              # 1.0 * 20
        goal_tags=["machine learning"],         # jaccard 0.5 * 15
        study_intensity="regular",              # 0.5 * 10
    )
    # 15 + 12.5 + 20 + 7.5 + 5 = 60
    assert compute_compatibility(me, other).score == 60


def test_reasons_are_grounded():
    me = _prof()
    score = compute_compatibility(me, _prof())
    joined = " ".join(score.reasons).lower()
    assert "evening" in joined
    assert "machine learning" in joined  # shared subject or goal


# ---- pre-filter + ranking + API ----

BASE_PROFILE = {
    "course": "CS", "year": 2, "subjects": ["Machine Learning", "Statistics"],
    "learning_style": "practice", "preferred_study_time": "evening",
    "study_environment": "quiet", "study_intensity": "intensive",
    "current_goal": "Prepare ML interview", "daily_goal_hours": 3,
    "motivation_type": "achievement", "experience_level": "intermediate",
}


def _register(client, email, name) -> str:
    r = client.post("/auth/register", json={"email": email, "password": "supersecret1", "name": name})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _set_profile(client, token, **overrides):
    payload = dict(BASE_PROFILE, **overrides)
    r = client.post("/profiles", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201, r.text


def test_list_matches_ranked_and_prefiltered(client):
    me = _register(client, "me@x.com", "me")
    _set_profile(client, me)  # CS, [ML, Stats], evening, practice, intensive

    twin = _register(client, "twin@x.com", "twin")
    _set_profile(client, twin)  # identical -> score 100

    cs2 = _register(client, "cs2@x.com", "cs2")
    _set_profile(client, cs2, subjects=["Biology"], preferred_study_time="morning",
                 learning_style="video", study_intensity="casual", current_goal=None)  # same course only

    other = _register(client, "math@x.com", "math")
    _set_profile(client, other, course="Mathematics", subjects=["Biology"],
                 preferred_study_time="morning", learning_style="video",
                 study_intensity="casual", current_goal=None)  # no course/subject overlap

    r = client.get("/matches", headers={"Authorization": f"Bearer {me}"})
    assert r.status_code == 200
    names = [m["partner"]["name"] for m in r.json()]

    assert "math" not in names          # excluded by the pre-filter
    assert "me" not in names            # never match yourself
    assert names[0] == "twin"           # highest score first
    assert r.json()[0]["score"] == 100
    assert "cs2" in names               # included (same course) even with score 0


def test_explanation_endpoint(client):
    me = _register(client, "me@x.com", "me")
    _set_profile(client, me)
    twin = _register(client, "twin@x.com", "twin")
    _set_profile(client, twin)

    matches = client.get("/matches", headers={"Authorization": f"Bearer {me}"}).json()
    twin_id = matches[0]["partner"]["user_id"]

    r = client.get(f"/matches/{twin_id}/explanation", headers={"Authorization": f"Bearer {me}"})
    assert r.status_code == 200
    body = r.json()
    assert body["score"] == 100
    assert body["explanation"]
    assert body["source"] == "fallback"   # no API key in tests


def test_matches_require_profile(auth_client):
    assert auth_client.get("/matches").status_code == 404


def test_matches_require_auth(client):
    assert client.get("/matches").status_code == 401
