"""
Domain enums.

Kept in one place because several layers share them: profiles validate
against them, and the matching engine (chunk 4) relies on their ordering
(e.g. study-time adjacency, intensity rank). Storing the .value (a plain
string) in the DB keeps rows human-readable and migration-friendly.
"""
from enum import StrEnum


class LearningStyle(StrEnum):
    READING = "reading"
    VIDEO = "video"
    PRACTICE = "practice"
    NOTES = "notes"
    GROUP = "group"


class StudyTime(StrEnum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


class StudyEnvironment(StrEnum):
    QUIET = "quiet"
    DISCUSSION = "discussion"
    ACCOUNTABILITY = "accountability"


class StudyIntensity(StrEnum):
    CASUAL = "casual"
    REGULAR = "regular"
    INTENSIVE = "intensive"


class MotivationType(StrEnum):
    ACHIEVEMENT = "achievement"
    SOCIAL = "social"
    DEADLINE = "deadline"
    GROWTH = "growth"


class ExperienceLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# --- Orderings used by the matching engine (chunk 4) ---

# Study-time buckets in clock order, so "adjacent" is well defined.
STUDY_TIME_ORDER: list[StudyTime] = [
    StudyTime.MORNING,
    StudyTime.AFTERNOON,
    StudyTime.EVENING,
    StudyTime.NIGHT,
]

# Intensity is ordinal: casual < regular < intensive.
INTENSITY_RANK: dict[StudyIntensity, int] = {
    StudyIntensity.CASUAL: 0,
    StudyIntensity.REGULAR: 1,
    StudyIntensity.INTENSIVE: 2,
}


# --- Tasks / Focus / Events (chunk 5) ---

class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class FocusMode(StrEnum):
    POMODORO = "pomodoro"
    DEEP_WORK = "deep_work"
    STOPWATCH = "stopwatch"


class EventType(StrEnum):
    TASK_CREATED = "TASK_CREATED"
    TASK_COMPLETED = "TASK_COMPLETED"
    SESSION_STARTED = "SESSION_STARTED"
    SESSION_COMPLETED = "SESSION_COMPLETED"
    ROOM_JOINED = "ROOM_JOINED"
    MATCH_ACCEPTED = "MATCH_ACCEPTED"


# --- Study rooms (chunk 8, Phase 2) ---

class RoomStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"


class PresenceStatus(StrEnum):
    ONLINE = "online"
    FOCUSING = "focusing"
    BREAK = "break"
    OFFLINE = "offline"
