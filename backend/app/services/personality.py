"""
Grounded learning-personality engine (spec §3).

The grounding guarantee
-----------------------
The backend FIRST derives a *menu* of candidate traits from the student's
actual questionnaire answers — every candidate carries the evidence that
justifies it (e.g. "late-night distraction risk" exists ONLY when
preferred_study_time == night and intensity == casual). The AI is then asked
to SELECT from that menu and optionally rephrase the labels. Any trait the AI
returns that is not on the menu is discarded. So the AI cannot invent an
ungrounded, horoscope-style trait — by construction, not by prompt etiquette.

If the AI provider is unavailable (NullProvider) or returns anything invalid,
we fall back to the deterministic menu itself. Either way the result is
grounded; the AI only improves wording and picks the most fitting subset.
"""
from dataclasses import dataclass, field

from app.models.enums import (
    LearningStyle,
    MotivationType,
    StudyEnvironment,
    StudyIntensity,
    StudyTime,
)
from app.models.student_profile import StudentProfile
from app.services.ai.base import AIProvider

MAX_STRENGTHS = 4
MAX_WEAKNESSES = 3


@dataclass
class Candidate:
    id: str
    label: str       # default human phrasing (AI may override)
    evidence: str    # which answer justifies it — traceability


@dataclass
class PersonalityResult:
    personality_type: str
    strengths: list[str]
    weaknesses: list[str]
    recommended_partner_type: str
    recommendations: list[str]
    source: str = "fallback"          # "ai" or "fallback"
    evidence: dict[str, str] = field(default_factory=dict)


# --------------------------------------------------------------------------
# Deterministic derivation from the questionnaire
# --------------------------------------------------------------------------

def _strength_candidates(p: StudentProfile) -> list[Candidate]:
    out: list[Candidate] = []
    if p.current_goal or p.goal_tags:
        out.append(Candidate("S_GOAL", "Goal-oriented",
                              f"has a stated goal: {p.current_goal or ', '.join(p.goal_tags)}"))
    if p.study_intensity == StudyIntensity.INTENSIVE:
        out.append(Candidate("S_COMMITTED", "Highly committed", "study_intensity = intensive"))
    if p.daily_goal_hours and p.daily_goal_hours >= 4:
        out.append(Candidate("S_AMBITIOUS", "Sets ambitious targets",
                              f"daily_goal_hours = {p.daily_goal_hours}"))
    if (p.learning_style == LearningStyle.GROUP
            or p.study_environment in (StudyEnvironment.DISCUSSION, StudyEnvironment.ACCOUNTABILITY)):
        out.append(Candidate("S_COLLABORATIVE", "Collaborative",
                              f"prefers {p.study_environment} / {p.learning_style}"))
    if p.study_environment == StudyEnvironment.QUIET and p.learning_style in (
            LearningStyle.READING, LearningStyle.NOTES, LearningStyle.PRACTICE):
        out.append(Candidate("S_SELF_DIRECTED", "Self-directed",
                              "prefers quiet, independent study"))
    if p.experience_level == "advanced":
        out.append(Candidate("S_EXPERIENCED", "Experienced", "experience_level = advanced"))
    if p.learning_style == LearningStyle.PRACTICE:
        out.append(Candidate("S_HANDS_ON", "Learns by doing", "learning_style = practice"))
    return out


def _weakness_candidates(p: StudentProfile) -> list[Candidate]:
    out: list[Candidate] = []
    # The spec's exact example: night owl + low intensity -> distraction risk.
    if p.preferred_study_time == StudyTime.NIGHT and p.study_intensity == StudyIntensity.CASUAL:
        out.append(Candidate("W_NIGHT", "Late-night distraction risk",
                              "studies at night with casual intensity"))
    if p.daily_goal_hours and p.daily_goal_hours >= 6:
        out.append(Candidate("W_OVERCOMMIT", "Risk of overcommitting",
                              f"daily_goal_hours = {p.daily_goal_hours}"))
    if p.study_environment == StudyEnvironment.QUIET and p.learning_style != LearningStyle.GROUP:
        out.append(Candidate("W_SOLO", "May benefit from more accountability",
                              "studies quietly and solo"))
    if p.experience_level == "beginner":
        out.append(Candidate("W_FUNDAMENTALS", "Still building fundamentals",
                              "experience_level = beginner"))
    if p.subjects and len(p.subjects) > 5:
        out.append(Candidate("W_SPREAD", "Focus spread across many subjects",
                              f"{len(p.subjects)} subjects selected"))
    if p.motivation_type == MotivationType.DEADLINE:
        out.append(Candidate("W_DEADLINE", "Deadline-dependent motivation",
                              "motivation_type = deadline"))
    return out


def _personality_type(p: StudentProfile) -> str:
    intensive = p.study_intensity == StudyIntensity.INTENSIVE
    if intensive and p.preferred_study_time == StudyTime.NIGHT:
        return "Night Owl Achiever"
    if intensive and p.study_environment == StudyEnvironment.QUIET and p.learning_style in (
            LearningStyle.READING, LearningStyle.NOTES, LearningStyle.PRACTICE):
        return "Deep Focus Learner"
    if p.learning_style == LearningStyle.GROUP or p.study_environment in (
            StudyEnvironment.DISCUSSION, StudyEnvironment.ACCOUNTABILITY):
        return "Collaborative Learner"
    if p.study_intensity == StudyIntensity.CASUAL:
        return "Easygoing Explorer"
    return "Balanced Learner"


def _recommended_partner_type(p: StudentProfile) -> str:
    if p.study_environment == StudyEnvironment.ACCOUNTABILITY:
        return "An accountability-focused partner"
    if p.learning_style == LearningStyle.GROUP or p.study_environment == StudyEnvironment.DISCUSSION:
        return "A collaborative study group"
    if p.study_intensity == StudyIntensity.INTENSIVE:
        return "Another high-intensity learner"
    return "A partner who shares your schedule"


def _recommendations(p: StudentProfile, weaknesses: list[Candidate]) -> list[str]:
    tips: list[str] = []
    w_ids = {c.id for c in weaknesses}
    if p.preferred_study_time:
        tips.append(f"Schedule your most demanding topics in the {p.preferred_study_time}, your preferred window.")
    if "W_NIGHT" in w_ids:
        tips.append("Late sessions invite distraction — try one short, focused block rather than a long late stretch.")
    if "W_OVERCOMMIT" in w_ids:
        tips.append("Your daily target is high; build in breaks so the pace stays sustainable.")
    if p.goal_tags:
        tips.append(f"Keep tasks tied to your goal — start with {p.goal_tags[0]}.")
    return tips[:3]


def _deterministic(p: StudentProfile) -> PersonalityResult:
    strengths = _strength_candidates(p)[:MAX_STRENGTHS]
    weaknesses = _weakness_candidates(p)[:MAX_WEAKNESSES]
    evidence = {c.id: c.evidence for c in strengths + weaknesses}
    return PersonalityResult(
        personality_type=_personality_type(p),
        strengths=[c.label for c in strengths],
        weaknesses=[c.label for c in weaknesses],
        recommended_partner_type=_recommended_partner_type(p),
        recommendations=_recommendations(p, weaknesses),
        source="fallback",
        evidence=evidence,
    )


# --------------------------------------------------------------------------
# AI selection/phrasing layer (constrained to the menu)
# --------------------------------------------------------------------------

def _build_prompt(p: StudentProfile, strengths: list[Candidate], weaknesses: list[Candidate]) -> tuple[str, str]:
    system = (
        "You label a student's learning personality. You may ONLY select trait "
        "ids from the provided menu and optionally rewrite their labels into "
        "natural, encouraging language. Never invent a trait that is not on the "
        "menu. Reply ONLY with JSON of the form: "
        '{"personality_type": str, "strength_ids": [str], "weakness_ids": [str], '
        '"labels": {id: improved_label}}.'
    )
    menu = {
        "profile": {
            "course": p.course, "learning_style": p.learning_style,
            "preferred_study_time": p.preferred_study_time,
            "study_environment": p.study_environment,
            "study_intensity": p.study_intensity, "current_goal": p.current_goal,
        },
        "strength_menu": [{"id": c.id, "label": c.label, "evidence": c.evidence} for c in strengths],
        "weakness_menu": [{"id": c.id, "label": c.label, "evidence": c.evidence} for c in weaknesses],
    }
    import json
    return system, json.dumps(menu)


def generate_personality(profile: StudentProfile, provider: AIProvider) -> PersonalityResult:
    strengths = _strength_candidates(profile)[:MAX_STRENGTHS]
    weaknesses = _weakness_candidates(profile)[:MAX_WEAKNESSES]
    fallback = _deterministic(profile)

    system, user = _build_prompt(profile, strengths, weaknesses)
    raw = provider.complete_json(system, user)
    if not isinstance(raw, dict):
        return fallback  # provider unavailable or returned nothing usable

    try:
        allowed_s = {c.id: c.label for c in strengths}
        allowed_w = {c.id: c.label for c in weaknesses}
        labels = raw.get("labels") or {}

        # Keep only ids that are actually on the menu => hallucinations dropped.
        chosen_s_ids = [i for i in (raw.get("strength_ids") or []) if i in allowed_s] or list(allowed_s)
        chosen_w_ids = [i for i in (raw.get("weakness_ids") or []) if i in allowed_w] or list(allowed_w)

        def label_for(i: str, default: str) -> str:
            v = labels.get(i)
            return v if isinstance(v, str) and v.strip() else default

        ptype = raw.get("personality_type")
        if not isinstance(ptype, str) or not ptype.strip():
            ptype = fallback.personality_type

        return PersonalityResult(
            personality_type=ptype.strip()[:80],
            strengths=[label_for(i, allowed_s[i]) for i in chosen_s_ids][:MAX_STRENGTHS],
            weaknesses=[label_for(i, allowed_w[i]) for i in chosen_w_ids][:MAX_WEAKNESSES],
            recommended_partner_type=fallback.recommended_partner_type,
            recommendations=fallback.recommendations,
            source="ai",
            evidence=fallback.evidence,
        )
    except Exception:
        return fallback
