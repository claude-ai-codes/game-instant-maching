import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.feedback import Rating
from app.models.room import RoomStatus


class RoomResponse(BaseModel):
    id: uuid.UUID
    recruitment_id: uuid.UUID
    status: RoomStatus
    expires_at: datetime
    created_at: datetime
    game: str | None = None
    region: str | None = None
    members: list["RoomMemberResponse"] = []

    model_config = {"from_attributes": True}


class RoomMemberResponse(BaseModel):
    user_id: uuid.UUID
    nickname: str
    role: str | None

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class MessageResponse(BaseModel):
    id: uuid.UUID
    room_id: uuid.UUID
    user_id: uuid.UUID
    content: str
    created_at: datetime
    nickname: str | None = None

    model_config = {"from_attributes": True}


class FeedbackCreate(BaseModel):
    to_user_id: uuid.UUID
    rating: Rating
