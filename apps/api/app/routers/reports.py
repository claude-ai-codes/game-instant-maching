from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.base import utcnow
from app.models.report import Report, ReportStatus
from app.models.room import Room, RoomMember
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.report import ReportCreate, ReportResponse
from app.services.moderation import check_content
from app.utils.validators import sanitize_text

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def create_report(
    request: Request,
    body: ReportCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Report:
    if body.reported_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot report yourself")

    # Verify reported user exists
    reported_user = await db.get(User, body.reported_id)
    if not reported_user:
        raise HTTPException(status_code=404, detail="Reported user not found")

    # Verify room exists and reporter is a member
    if body.room_id:
        room = await db.get(Room, body.room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        membership = await db.execute(
            select(RoomMember).where(
                RoomMember.room_id == body.room_id,
                RoomMember.user_id == user.id,
            )
        )
        if not membership.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="You are not a member of this room")

    reason = sanitize_text(body.reason)
    check_content(reason, "reason")

    report = Report(
        reporter_id=user.id,
        reported_id=body.reported_id,
        room_id=body.room_id,
        reason=reason,
    )
    db.add(report)
    await db.flush()

    # Auto-suspend if report threshold is reached
    report_count_result = await db.execute(
        select(func.count()).select_from(Report).where(
            Report.reported_id == body.reported_id,
            Report.status == ReportStatus.pending,
        )
    )
    report_count = report_count_result.scalar() or 0

    if report_count >= settings.report_threshold_for_suspension:
        now = utcnow()
        # Only set suspension if not already suspended further out
        if not reported_user.suspended_until or reported_user.suspended_until < now:
            reported_user.suspended_until = now + timedelta(
                hours=settings.suspension_duration_hours
            )

    await db.commit()
    await db.refresh(report)
    return report
