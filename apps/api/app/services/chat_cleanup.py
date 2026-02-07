import asyncio
import logging
from datetime import timedelta

from sqlalchemy import delete, update

from app.config import settings
from app.database import async_session
from app.models.base import utcnow
from app.models.message import Message
from app.models.recruitment import Recruitment, RecruitmentStatus
from app.models.room import Room, RoomStatus

logger = logging.getLogger(__name__)


async def cleanup_expired_messages() -> int:
    cutoff = utcnow() - timedelta(hours=settings.message_ttl_hours)
    async with async_session() as db:
        result = await db.execute(delete(Message).where(Message.created_at < cutoff))
        await db.commit()
        count = result.rowcount
        if count:
            logger.info("Deleted %d expired messages", count)
        return count


async def expire_recruitments() -> int:
    now = utcnow()
    async with async_session() as db:
        result = await db.execute(
            update(Recruitment)
            .where(
                Recruitment.status == RecruitmentStatus.open,
                Recruitment.expires_at <= now,
            )
            .values(status=RecruitmentStatus.expired)
        )
        await db.commit()
        count = result.rowcount
        if count:
            logger.info("Expired %d recruitments", count)
        return count


async def expire_rooms() -> int:
    now = utcnow()
    async with async_session() as db:
        result = await db.execute(
            update(Room)
            .where(Room.status == RoomStatus.active, Room.expires_at <= now)
            .values(status=RoomStatus.expired)
        )
        await db.commit()
        count = result.rowcount
        if count:
            logger.info("Expired %d rooms", count)
        return count


async def run_periodic_cleanup(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            await cleanup_expired_messages()
            await expire_recruitments()
            await expire_rooms()
        except Exception:
            logger.exception("Error in periodic cleanup")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=300)
        except asyncio.TimeoutError:
            pass
