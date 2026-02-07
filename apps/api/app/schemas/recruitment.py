import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.recruitment import RecruitmentStatus


class RecruitmentCreate(BaseModel):
    game: str = Field(max_length=50)
    region: str = Field(max_length=20)
    start_time: datetime
    desired_role: str | None = Field(default=None, max_length=50)
    memo: str | None = Field(default=None, max_length=200)


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
