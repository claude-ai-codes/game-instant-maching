import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.base import utcnow
from app.models.recruitment import Recruitment, RecruitmentStatus
from app.models.report import Report, ReportStatus
from app.models.room import Room, RoomStatus
from app.models.user import User
from app.schemas.admin import (
    AdminReportResponse,
    AdminStatsResponse,
    AdminUserResponse,
    SuspendRequest,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def verify_admin(x_admin_secret: str = Header(...)) -> None:
    if not settings.admin_secret:
        raise HTTPException(status_code=503, detail="Admin not configured")
    if x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Invalid admin secret")


# --- Reports ---


@router.get("/reports", response_model=list[AdminReportResponse])
async def list_reports(
    _: None = Depends(verify_admin),
    report_status: ReportStatus | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[AdminReportResponse]:
    stmt = select(Report).order_by(Report.created_at.desc()).offset(offset).limit(limit)
    if report_status:
        stmt = stmt.where(Report.status == report_status)
    result = await db.execute(stmt)
    return [AdminReportResponse.model_validate(r) for r in result.scalars().all()]


@router.patch("/reports/{report_id}")
async def update_report_status(
    report_id: uuid.UUID,
    new_status: ReportStatus,
    _: None = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = new_status
    await db.commit()
    return {"detail": f"Report status updated to {new_status.value}"}


# --- Users ---


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: uuid.UUID,
    _: None = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    report_count_result = await db.execute(
        select(func.count()).select_from(Report).where(Report.reported_id == user_id)
    )
    report_count = report_count_result.scalar() or 0

    return AdminUserResponse(
        id=user.id,
        nickname=user.nickname,
        is_active=user.is_active,
        is_banned=user.is_banned,
        suspended_until=user.suspended_until,
        created_at=user.created_at,
        report_count=report_count,
    )


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: uuid.UUID,
    body: SuspendRequest,
    _: None = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.suspended_until = utcnow() + timedelta(hours=body.duration_hours)
    await db.commit()
    return {"detail": f"User suspended for {body.duration_hours} hours"}


@router.post("/users/{user_id}/ban")
async def ban_user(
    user_id: uuid.UUID,
    _: None = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_banned = True
    user.is_active = False
    await db.commit()
    return {"detail": "User banned"}


@router.post("/users/{user_id}/unban")
async def unban_user(
    user_id: uuid.UUID,
    _: None = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_banned = False
    user.suspended_until = None
    await db.commit()
    return {"detail": "User unbanned"}


# --- Stats / Monitoring ---


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    _: None = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminStatsResponse:
    now = utcnow()

    active_rooms = await db.execute(
        select(func.count()).select_from(Room).where(Room.status == RoomStatus.active)
    )
    open_recruitments = await db.execute(
        select(func.count())
        .select_from(Recruitment)
        .where(Recruitment.status == RecruitmentStatus.open, Recruitment.expires_at > now)
    )
    pending_reports = await db.execute(
        select(func.count())
        .select_from(Report)
        .where(Report.status == ReportStatus.pending)
    )
    total_users = await db.execute(select(func.count()).select_from(User))
    banned_users = await db.execute(
        select(func.count()).select_from(User).where(User.is_banned.is_(True))
    )

    return AdminStatsResponse(
        active_rooms=active_rooms.scalar() or 0,
        open_recruitments=open_recruitments.scalar() or 0,
        pending_reports=pending_reports.scalar() or 0,
        total_users=total_users.scalar() or 0,
        banned_users=banned_users.scalar() or 0,
    )
