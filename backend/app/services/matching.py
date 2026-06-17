"""
Partner matching engine (spec §4).

Scoring is fully deterministic — AI is NEVER used to compute matches, only to
phrase the explanation. The compatibility score (0–100) is a weighted sum:

    schedule_match  30%   preferred_study_time: exact 1.0 / adjacent 0.5 / else 0
    subject_match   25%   Jaccard overlap of subjects
    learning_style  20%   exact 1.0 / else 0
    goal_similarity 15%   Jaccard overlap of goal_tags
    study_intensity 10%   ordinal: 1 - |rank_a - rank_b| / 2

Scalability: we never score the whole table. `find_candidates` first reduces
the set with an indexed query (course btree OR subjects GIN array-overlap),
then we score only that subset.
"""
from dataclasses import asdict, dataclass

from sqlalchemy import String, cast, or_, select
from sqlalchemy.dialects.postgresql import ARRAY as PGARRAY
from sqlalchemy.orm import Session

from app.models.enums import INTENSITY_RANK, STUDY_TIME_ORDER, StudyIntensity, StudyTime
from app.models.student_profile import StudentProfile
from app.services.ai.base import AIProvider

WEIGHTS = {
    "schedule_match": 0.30,
    "subject_match": 0.25,
    "learning_style": 0.20,
    "goal_similarity": 0.15,
    "study_intensity": 0.10,
}


@dataclass
class MatchComponents:
    schedule_match: float
    subject_match: float
    learning_style: float
    goal_similarity: float
    study_intensity: float


@dataclass
class MatchScore:
    score: int
    components: MatchComponents
    reasons: list[str]
    shared_subjects: list[str]
    shared_goal_tags: list[str]


# ---- component functions ----

def _jaccard(a: list[str] | None, b: list[str] | None) -> tuple[float, set[str]]:
    A, B = set(a or []), set(b or [])
    union = A | B
    if not union:
        return 0.0, set()
    inter = A & B
    return len(inter) / len(union), inter


def _schedule_match(a: str, b: str) -> float:
    try:
        ia = STUDY_TIME_ORDER.index(StudyTime(a))
        ib = STUDY_TIME_ORDER.index(StudyTime(b))
    except ValueError:
        return 0.0
    dist = abs(ia - ib)
    if dist == 0:
        return 1.0
    if dist == 1:
        return 0.5
    return 0.0


def _style_match(a: str, b: str) -> float:
    return 1.0 if a == b else 0.0


def _intensity_match(a: str, b: str) -> float:
    try:
        ra = INTENSITY_RANK[StudyIntensity(a)]
        rb = INTENSITY_RANK[StudyIntensity(b)]
    except (ValueError, KeyError):
        return 0.0
    return 1.0 - abs(ra - rb) / 2  # 0,1,2 steps -> 1.0, 0.5, 0.0


def compute_compatibility(me: StudentProfile, other: StudentProfile) -> MatchScore:
    schedule = _schedule_match(me.preferred_study_time, other.preferred_study_time)
    subject, shared_subjects = _jaccard(me.subjects, other.subjects)
    style = _style_match(me.learning_style, other.learning_style)
    goal, shared_goals = _jaccard(me.goal_tags, other.goal_tags)
    intensity = _intensity_match(me.study_intensity, other.study_intensity)

    components = MatchComponents(
        schedule_match=round(schedule, 3),
        subject_match=round(subject, 3),
        learning_style=round(style, 3),
        goal_similarity=round(goal, 3),
        study_intensity=round(intensity, 3),
    )
    total = (
        schedule * WEIGHTS["schedule_match"]
        + subject * WEIGHTS["subject_match"]
        + style * WEIGHTS["learning_style"]
        + goal * WEIGHTS["goal_similarity"]
        + intensity * WEIGHTS["study_intensity"]
    )
    score = round(total * 100)

    reasons: list[str] = []
    if schedule == 1.0:
        reasons.append(f"you both study in the {me.preferred_study_time}")
    elif schedule == 0.5:
        reasons.append(f"your study times are close ({me.preferred_study_time}/{other.preferred_study_time})")
    if shared_subjects:
        reasons.append("you share " + ", ".join(sorted(shared_subjects)))
    if style == 1.0:
        reasons.append(f"you both prefer {me.learning_style} learning")
    if shared_goals:
        reasons.append("shared goals: " + ", ".join(sorted(shared_goals)))
    if intensity >= 0.5:
        reasons.append(f"similar study intensity ({me.study_intensity}/{other.study_intensity})")

    return MatchScore(
        score=score,
        components=components,
        reasons=reasons,
        shared_subjects=sorted(shared_subjects),
        shared_goal_tags=sorted(shared_goals),
    )


# ---- candidate pre-filter (the scalability step) ----

def find_candidates(db: Session, me: StudentProfile) -> list[StudentProfile]:
    """Cheap, indexed reduction BEFORE scoring: same course OR overlapping
    subjects. On Postgres this uses the btree(course) + GIN(subjects) indexes;
    on SQLite (tests) we fall back to an in-Python filter."""
    base = select(StudentProfile).where(StudentProfile.user_id != me.user_id)

    if db.get_bind().dialect.name == "postgresql":
        stmt = base.where(
            or_(
                StudentProfile.course == me.course,
                StudentProfile.subjects.op("&&")(cast(me.subjects, PGARRAY(String))),
            )
        )
        return list(db.scalars(stmt))

    # Portable fallback for SQLite / tests.
    my_subjects = set(me.subjects or [])
    return [
        p for p in db.scalars(base)
        if p.course == me.course or (my_subjects & set(p.subjects or []))
    ]


def rank_matches(db: Session, me: StudentProfile, limit: int = 10) -> list[tuple[StudentProfile, MatchScore]]:
    scored = [(p, compute_compatibility(me, p)) for p in find_candidates(db, me)]
    scored.sort(key=lambda t: t[1].score, reverse=True)
    return scored[:limit]


# ---- AI explanation (grounded in the deterministic reasons) ----

def explain_match(me: StudentProfile, other: StudentProfile, score: MatchScore,
                  provider: AIProvider) -> tuple[str, str]:
    if not score.reasons:
        return ("You have a little overlap in study preferences — worth a try.", "fallback")

    fallback = "Matched because " + "; ".join(score.reasons) + "."

    import json
    system = (
        "Write ONE short, friendly sentence (max 30 words) explaining why two "
        "students are a good study match. Use ONLY the supplied reasons; do not "
        'invent shared traits. Reply as JSON: {"explanation": str}.'
    )
    user = json.dumps({"score": score.score, "reasons": score.reasons})
    raw = provider.complete_json(system, user)
    if isinstance(raw, dict) and isinstance(raw.get("explanation"), str) and raw["explanation"].strip():
        return (raw["explanation"].strip()[:300], "ai")
    return (fallback, "fallback")


def score_to_dict(score: MatchScore) -> dict:
    d = asdict(score)
    return d
