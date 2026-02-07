import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    nickname: str = Field(min_length=2, max_length=20)
    turnstile_token: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    nickname: str
    created_at: datetime

    model_config = {"from_attributes": True}
