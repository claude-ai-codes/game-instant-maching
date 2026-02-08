import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.feedback import Feedback
from app.models.message import Message
from app.models.recruitment import Recruitment
from app.models.room import Room, RoomMember, RoomStatus
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.room import (
    FeedbackCreate,
    MessageCreate,
    MessageResponse,
    RoomMemberResponse,
    RoomResponse,
)
from app.services.moderation import check_content
from app.utils.validators import sanitize_text
from app.websocket import manager

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


async def _get_room_or_404(room_id: uuid.UUID, db: AsyncSession) -> Room:
    room = await db.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


async def _check_membership(room_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> None:
    result = await db.execute(
        select(RoomMember).where(RoomMember.room_id == room_id, RoomMember.user_id == user_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this room")


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoomResponse:
    room = await _get_room_or_404(room_id, db)
    await _check_membership(room_id, user.id, db)

    # Get members
    members_result = await db.execute(
        select(RoomMember, User.nickname)
        .join(User, User.id == RoomMember.user_id)
        .where(RoomMember.room_id == room_id)
    )
    members = [
        RoomMemberResponse(
            user_id=m.user_id, nickname=nickname, role=m.role, ready_to_close=m.ready_to_close
        )
        for m, nickname in members_result.all()
    ]

    # Get recruitment info
    recruitment = await db.get(Recruitment, room.recruitment_id)

    return RoomResponse(
        id=room.id,
        recruitment_id=room.recruitment_id,
        status=room.status,
        expires_at=room.expires_at,
        created_at=room.created_at,
        game=recruitment.game if recruitment else None,
        region=recruitment.region if recruitment else None,
        members=members,
    )


@router.get("/{room_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    room_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MessageResponse]:
    await _get_room_or_404(room_id, db)
    await _check_membership(room_id, user.id, db)

    result = await db.execute(
        select(Message, User.nickname)
        .join(User, User.id == Message.user_id)
        .where(Message.room_id == room_id)
        .order_by(Message.created_at.asc())
    )
    return [
        MessageResponse(
            id=m.id,
            room_id=m.room_id,
            user_id=m.user_id,
            content=m.content,
            created_at=m.created_at,
            nickname=nickname,
        )
        for m, nickname in result.all()
    ]


@router.post(
    "/{room_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("20/minute")
async def send_message(
    request: Request,
    room_id: uuid.UUID,
    body: MessageCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    room = await _get_room_or_404(room_id, db)
    if room.status != RoomStatus.active:
        raise HTTPException(status_code=400, detail="Room is not active")
    await _check_membership(room_id, user.id, db)

    content = sanitize_text(body.content)
    check_content(content, "message")

    msg = Message(room_id=room_id, user_id=user.id, content=content)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    response = MessageResponse(
        id=msg.id,
        room_id=msg.room_id,
        user_id=msg.user_id,
        content=msg.content,
        created_at=msg.created_at,
        nickname=user.nickname,
    )

    # Notify room members via WebSocket
    members_result = await db.execute(
        select(RoomMember.user_id).where(RoomMember.room_id == room_id)
    )
    member_ids = [row[0] for row in members_result.all()]
    await manager.send_to_users(
        member_ids,
        {"type": "new_message", "data": {"room_id": str(room_id)}},
    )

    return response


@router.post("/{room_id}/close")
@limiter.limit("5/minute")
async def close_room(
    request: Request,
    room_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    room = await _get_room_or_404(room_id, db)
    if room.status != RoomStatus.active:
        raise HTTPException(status_code=400, detail="Room is not active")
    await _check_membership(room_id, user.id, db)

    # Get the requesting user's membership
    my_member_result = await db.execute(
        select(RoomMember).where(
            RoomMember.room_id == room_id, RoomMember.user_id == user.id
        )
    )
    my_member = my_member_result.scalar_one()

    if my_member.ready_to_close:
        raise HTTPException(status_code=400, detail="You already requested close")

    my_member.ready_to_close = True

    # Check if all members are ready
    all_members_result = await db.execute(
        select(RoomMember).where(RoomMember.room_id == room_id)
    )
    all_members = list(all_members_result.scalars().all())
    member_ids = [m.user_id for m in all_members]
    all_ready = all(m.ready_to_close for m in all_members)

    if all_ready:
        room.status = RoomStatus.closed
        await db.commit()
        await manager.send_to_users(
            member_ids,
            {"type": "room_closed", "data": {"room_id": str(room_id)}},
        )
        return {"detail": "Room closed", "status": "closed"}

    await db.commit()
    await manager.send_to_users(
        member_ids,
        {"type": "close_requested", "data": {"room_id": str(room_id), "user_id": str(user.id)}},
    )
    return {"detail": "Waiting for other member to close", "status": "pending_close"}


@router.post("/{room_id}/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    room_id: uuid.UUID,
    body: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    room = await _get_room_or_404(room_id, db)
    if room.status not in (RoomStatus.closed, RoomStatus.expired):
        raise HTTPException(status_code=400, detail="Room must be closed first")
    await _check_membership(room_id, user.id, db)

    # Check target is also a member
    await _check_membership(room_id, body.to_user_id, db)

    if body.to_user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot give feedback to yourself")

    # Check duplicate
    existing = await db.execute(
        select(Feedback).where(
            Feedback.room_id == room_id, Feedback.from_user_id == user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Feedback already submitted")

    feedback = Feedback(
        room_id=room_id,
        from_user_id=user.id,
        to_user_id=body.to_user_id,
        rating=body.rating,
    )
    db.add(feedback)
    await db.commit()
    return {"detail": "Feedback submitted"}


@router.get("/pending-feedback", response_model=list[dict])
async def get_pending_feedback_rooms(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Return closed/expired rooms where the user has not yet submitted feedback."""
    # Find rooms user is a member of that are closed/expired
    closed_rooms_stmt = (
        select(Room.id)
        .join(RoomMember, RoomMember.room_id == Room.id)
        .where(
            RoomMember.user_id == user.id,
            Room.status.in_([RoomStatus.closed, RoomStatus.expired]),
        )
    )
    # Exclude rooms where user already gave feedback
    already_feedbacked = select(Feedback.room_id).where(Feedback.from_user_id == user.id)
    stmt = (
        select(Room.id)
        .where(Room.id.in_(closed_rooms_stmt), Room.id.not_in(already_feedbacked))
        .order_by(Room.created_at.desc())
        .limit(5)
    )
    result = await db.execute(stmt)
    room_ids = result.scalars().all()
    return [{"room_id": str(rid)} for rid in room_ids]
