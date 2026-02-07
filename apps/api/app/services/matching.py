import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings as app_settings
from app.models.base import utcnow
from app.models.block import Block
from app.models.recruitment import Recruitment, RecruitmentStatus
from app.models.room import Room, RoomMember, RoomStatus
from app.websocket import manager


async def find_match_and_create_room(
    db: AsyncSession,
    recruitment: Recruitment,
    joiner_id: uuid.UUID,
) -> Room | None:
    """
    Try to match a joiner to an open recruitment.
    Uses SELECT ... FOR UPDATE SKIP LOCKED to prevent race conditions.
    Returns the created Room or None if match cannot be made.
    """
    now = utcnow()

    # Check the recruitment is still open (with lock on PostgreSQL)
    stmt = select(Recruitment).where(
        Recruitment.id == recruitment.id,
        Recruitment.status == RecruitmentStatus.open,
        Recruitment.expires_at > now,
    )
    # SQLite doesn't support FOR UPDATE
    dialect = db.bind.dialect.name if db.bind else ""
    if dialect != "sqlite":
        stmt = stmt.with_for_update(skip_locked=True)
    result = await db.execute(stmt)
    locked_recruitment = result.scalar_one_or_none()
    if not locked_recruitment:
        return None

    # Check blocker/blocked relationship
    block_check = await db.execute(
        select(Block).where(
            (
                (Block.blocker_id == locked_recruitment.user_id)
                & (Block.blocked_id == joiner_id)
            )
            | (
                (Block.blocker_id == joiner_id)
                & (Block.blocked_id == locked_recruitment.user_id)
            )
        )
    )
    if block_check.scalar_one_or_none():
        return None

    # Check joiner doesn't already have an active room
    active_room_check = await db.execute(
        select(RoomMember)
        .join(Room, Room.id == RoomMember.room_id)
        .where(RoomMember.user_id == joiner_id, Room.status == RoomStatus.active)
    )
    if active_room_check.scalar_one_or_none():
        return None

    # Check owner doesn't already have an active room
    owner_room_check = await db.execute(
        select(RoomMember)
        .join(Room, Room.id == RoomMember.room_id)
        .where(RoomMember.user_id == locked_recruitment.user_id, Room.status == RoomStatus.active)
    )
    if owner_room_check.scalar_one_or_none():
        return None

    # Create room
    locked_recruitment.status = RecruitmentStatus.matched
    room = Room(
        recruitment_id=locked_recruitment.id,
        status=RoomStatus.active,
        expires_at=now + timedelta(hours=app_settings.room_expiry_hours),
    )
    db.add(room)
    await db.flush()

    # Add members
    owner_member = RoomMember(
        room_id=room.id,
        user_id=locked_recruitment.user_id,
        role=locked_recruitment.desired_role,
    )
    joiner_member = RoomMember(room_id=room.id, user_id=joiner_id)
    db.add_all([owner_member, joiner_member])
    await db.commit()
    await db.refresh(room)

    # Notify both users via WebSocket
    await manager.send_to_users(
        [locked_recruitment.user_id, joiner_id],
        {"type": "match_created", "data": {"room_id": str(room.id)}},
    )
    await manager.broadcast_to_lobby(
        {
            "type": "recruitment_update",
            "data": {"action": "matched", "recruitment_id": str(locked_recruitment.id)},
        },
    )

    return room
