import hashlib
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.base import utcnow
from app.models.recruitment import Recruitment, RecruitmentStatus
from app.models.room import Room, RoomMember, RoomStatus
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.recruitment import RecruitmentCreate, RecruitmentResponse
from app.services.matching import find_match_and_create_room
from app.services.moderation import check_content
from app.utils.validators import sanitize_text, validate_game, validate_region
from app.websocket import manager


def _compute_ip_hash(request: Request) -> str | None:
    if request.client:
        return hashlib.sha256(request.client.host.encode()).hexdigest()
    return None

router = APIRouter(prefix="/api/recruitments", tags=["recruitments"])


@router.get("", response_model=list[RecruitmentResponse])
async def list_recruitments(
    db: AsyncSession = Depends(get_db),
) -> list[RecruitmentResponse]:
    now = utcnow()
    stmt = (
        select(Recruitment, User.nickname)
        .join(User, User.id == Recruitment.user_id)
        .where(Recruitment.status == RecruitmentStatus.open, Recruitment.expires_at > now)
        .order_by(Recruitment.created_at.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        RecruitmentResponse.model_validate(
            {**r.__dict__, "nickname": nickname}
        )
        for r, nickname in rows
    ]


@router.post("", response_model=RecruitmentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
async def create_recruitment(
    request: Request,
    body: RecruitmentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecruitmentResponse:
    if not validate_game(body.game):
        raise HTTPException(status_code=400, detail="Invalid game")
    if not validate_region(body.region):
        raise HTTPException(status_code=400, detail="Invalid region")

    if body.memo:
        check_content(body.memo, "memo")
    if body.desired_role:
        check_content(body.desired_role, "desired_role")

    # Check user doesn't already have an active room
    active_room = await db.execute(
        select(RoomMember)
        .join(Room, Room.id == RoomMember.room_id)
        .where(RoomMember.user_id == user.id, Room.status == RoomStatus.active)
    )
    if active_room.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already have an active room")

    # Check user doesn't already have an open recruitment
    open_recruitment = await db.execute(
        select(Recruitment).where(
            Recruitment.user_id == user.id,
            Recruitment.status == RecruitmentStatus.open,
        )
    )
    if open_recruitment.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="You already have an open recruitment")

    now = utcnow()

    # Fingerprint dedup: reject if same IP created same game+region within 5 min
    ip_hash = _compute_ip_hash(request)
    if ip_hash:
        recent_dup = await db.execute(
            select(Recruitment).where(
                Recruitment.ip_hash == ip_hash,
                Recruitment.game == body.game,
                Recruitment.region == body.region,
                Recruitment.status == RecruitmentStatus.open,
                Recruitment.created_at > now - timedelta(minutes=5),
            )
        )
        if recent_dup.scalar_one_or_none():
            raise HTTPException(
                status_code=429,
                detail="Similar recruitment created recently. Please wait a few minutes.",
            )

    recruitment = Recruitment(
        user_id=user.id,
        game=body.game,
        region=body.region,
        start_time=body.start_time,
        desired_role=sanitize_text(body.desired_role) if body.desired_role else None,
        memo=sanitize_text(body.memo) if body.memo else None,
        ip_hash=ip_hash,
        status=RecruitmentStatus.open,
        expires_at=now + timedelta(minutes=settings.recruitment_expiry_minutes),
    )
    db.add(recruitment)
    await db.commit()
    await db.refresh(recruitment)

    response = RecruitmentResponse.model_validate(
        {**recruitment.__dict__, "nickname": user.nickname}
    )

    await manager.broadcast_to_lobby({
        "type": "recruitment_update",
        "data": {"action": "created", "recruitment_id": str(recruitment.id)},
    })

    return response


@router.post("/{recruitment_id}/join")
@limiter.limit("10/hour")
async def join_recruitment(
    request: Request,
    recruitment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    recruitment = await db.get(Recruitment, recruitment_id)
    if not recruitment:
        raise HTTPException(status_code=404, detail="Recruitment not found")
    if recruitment.status != RecruitmentStatus.open:
        raise HTTPException(status_code=400, detail="Recruitment is not open")
    if recruitment.user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot join your own recruitment")

    room = await find_match_and_create_room(db, recruitment, user.id)
    if not room:
        raise HTTPException(status_code=409, detail="Match could not be created")

    return {"detail": "Matched", "room_id": str(room.id)}


@router.delete("/{recruitment_id}")
async def cancel_recruitment(
    recruitment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    recruitment = await db.get(Recruitment, recruitment_id)
    if not recruitment:
        raise HTTPException(status_code=404, detail="Recruitment not found")
    if recruitment.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your recruitment")
    if recruitment.status != RecruitmentStatus.open:
        raise HTTPException(status_code=400, detail="Recruitment is not open")

    recruitment.status = RecruitmentStatus.cancelled
    await db.commit()

    await manager.broadcast_to_lobby({
        "type": "recruitment_update",
        "data": {"action": "cancelled", "recruitment_id": str(recruitment.id)},
    })

    return {"detail": "Cancelled"}
