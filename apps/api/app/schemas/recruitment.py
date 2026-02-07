import uuid
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field, field_validator

from app.models.recruitment import RecruitmentStatus


class RecruitmentCreate(BaseModel):
    game: str = Field(max_length=50)
    region: str = Field(max_length=20)
    start_time: datetime
    desired_role: str | None = Field(default=None, max_length=50)
    memo: str | None = Field(default=None, max_length=200)

    @field_validator("start_time")
    @classmethod
    def start_time_not_in_past(cls, v: datetime) -> datetime:
        now = datetime.now(timezone.utc)
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v < now - timedelta(minutes=5):
            raise ValueError("start_time must not be in the past")
        return v


class RecruitmentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    game: str
    region: str
    start_time: datetime
    desired_role: str | None
    memo: str | None
    status: RecruitmentStatus
    expires_at: datetime
    created_at: datetime
    nickname: str | None = None

    model_config = {"from_attributes": True}
