import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AIProfilePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    personality_type: str
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    recommended_partner_type: str
    source: str           # "ai" | "fallback"
    created_at: datetime
    updated_at: datetime
