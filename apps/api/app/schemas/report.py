import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.report import ReportStatus


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
    status: ReportStatus
    created_at: datetime

    model_config = {"from_attributes": True}
