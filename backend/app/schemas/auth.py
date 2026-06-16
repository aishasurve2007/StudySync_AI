"""
Pydantic schemas = the API's public contract.

These are intentionally separate from the ORM models. The ORM is how we
store data; schemas are what we accept and return over HTTP. Keeping them
apart means we never accidentally leak a field like `password_hash`, and
we can validate input (email format, password length) before it touches
the database.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=120)
    timezone: str = Field(default="UTC", max_length=64)  # IANA string, e.g. "Asia/Kolkata"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    # from_attributes lets us build this straight from a SQLAlchemy User object.
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    name: str
    avatar: str | None
    timezone: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
