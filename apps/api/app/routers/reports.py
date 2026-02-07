from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.report import Report
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

    reason = sanitize_text(body.reason)
    check_content(reason, "reason")

    report = Report(
        reporter_id=user.id,
        reported_id=body.reported_id,
        room_id=body.room_id,
        reason=reason,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report
