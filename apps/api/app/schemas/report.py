import uuid

from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    reported_id: uuid.UUID
    room_id: uuid.UUID | None = None
    reason: str = Field(min_length=1, max_length=500)


class ReportResponse(BaseModel):
    id: uuid.UUID
    reporter_id: uuid.UUID
    reported_id: uuid.UUID
    room_id: uuid.UUID | None
    reason: str

    model_config = {"from_attributes": True}
