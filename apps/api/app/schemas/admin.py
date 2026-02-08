import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.report import ReportStatus


class AdminReportResponse(BaseModel):
    id: uuid.UUID
    reporter_id: uuid.UUID
    reported_id: uuid.UUID
    room_id: uuid.UUID | None
    reason: str
    status: ReportStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    nickname: str
    is_active: bool
    is_banned: bool
    suspended_until: datetime | None
    created_at: datetime
    report_count: int


class SuspendRequest(BaseModel):
    duration_hours: int = Field(ge=1, le=8760)  # max 1 year


class AdminStatsResponse(BaseModel):
    active_rooms: int
    open_recruitments: int
    pending_reports: int
    total_users: int
    banned_users: int
