import uuid

from pydantic import BaseModel


class MatchPartner(BaseModel):
    user_id: uuid.UUID
    name: str
    avatar: str | None
    course: str


class MatchComponentsOut(BaseModel):
    schedule_match: float
    subject_match: float
    learning_style: float
    goal_similarity: float
    study_intensity: float


class MatchOut(BaseModel):
    partner: MatchPartner
    score: int                       # 0–100
    components: MatchComponentsOut
    reasons: list[str]
    shared_subjects: list[str]
    shared_goal_tags: list[str]


class MatchExplanationOut(BaseModel):
    partner_id: uuid.UUID
    score: int
    explanation: str
    source: str                      # "ai" | "fallback"
