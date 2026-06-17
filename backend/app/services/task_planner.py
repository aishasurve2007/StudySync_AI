"""
AI task planner (spec §6).

Input: a goal + a deadline in days. The AI returns a structured list of tasks
with priority and an *AI-estimated* time per task. As everywhere else, there's
a deterministic fallback so the planner works with no API key — it builds a
sensible study plan from the goal text / goal tags.
"""
import json
from dataclasses import dataclass

from app.models.enums import TaskPriority
from app.services.ai.base import AIProvider

_MIN_TIME, _MAX_TIME = 15, 240


@dataclass
class PlannedTask:
    title: str
    priority: str
    estimated_time: int  # minutes


def _clamp_time(v) -> int:
    try:
        return max(_MIN_TIME, min(int(v), _MAX_TIME))
    except (TypeError, ValueError):
        return 60


def _valid_priority(v) -> str:
    return v if v in (p.value for p in TaskPriority) else TaskPriority.MEDIUM.value


def _fallback_plan(goal: str, deadline_days: int, goal_tags: list[str] | None) -> list[PlannedTask]:
    # Prefer a subject-like tag (e.g. "machine learning") over a process word
    # (e.g. "interview"/"exam") so the plan reads naturally.
    process_words = {"interview", "exam", "certification", "project", "test"}
    topic = goal or "your goal"
    if goal_tags:
        subject_tags = [t for t in goal_tags if t not in process_words]
        topic = (subject_tags or goal_tags)[0]
    topic = topic.strip()
    # A simple, defensible study arc; earlier stages get higher priority.
    template = [
        (f"Review the fundamentals of {topic}", "high", 90),
        (f"Work through practice problems on {topic}", "high", 90),
        (f"Summarise key concepts of {topic} into notes", "medium", 60),
        (f"Do a timed mock / past paper on {topic}", "medium", 90),
        (f"Revise weak areas and self-test on {topic}", "low", 60),
    ]
    # Fewer tasks for very short deadlines.
    n = 3 if deadline_days <= 3 else len(template)
    return [PlannedTask(t, p, _clamp_time(m)) for (t, p, m) in template[:n]]


def plan_tasks(goal: str, deadline_days: int, goal_tags: list[str] | None,
               provider: AIProvider) -> tuple[list[PlannedTask], str]:
    fallback = _fallback_plan(goal, deadline_days, goal_tags)

    system = (
        "You are a study planner. Given a goal and a deadline in days, produce "
        "4–7 concrete, actionable study tasks. Estimate minutes per task. "
        'Reply ONLY as JSON: {"tasks": [{"task": str, "priority": '
        '"low"|"medium"|"high", "estimated_time": int_minutes}]}.'
    )
    user = json.dumps({"goal": goal, "deadline_days": deadline_days})
    raw = provider.complete_json(system, user)

    if isinstance(raw, dict) and isinstance(raw.get("tasks"), list) and raw["tasks"]:
        planned: list[PlannedTask] = []
        for item in raw["tasks"][:7]:
            if not isinstance(item, dict):
                continue
            title = item.get("task") or item.get("title")
            if not isinstance(title, str) or not title.strip():
                continue
            planned.append(PlannedTask(
                title=title.strip()[:200],
                priority=_valid_priority(item.get("priority")),
                estimated_time=_clamp_time(item.get("estimated_time")),
            ))
        if planned:
            return planned, "ai"

    return fallback, "fallback"
