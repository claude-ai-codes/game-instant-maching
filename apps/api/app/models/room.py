import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, new_uuid


class RoomStatus(str, enum.Enum):
    active = "active"
    closed = "closed"
    expired = "expired"


class Room(Base, TimestampMixin):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    recruitment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recruitments.id"), nullable=False, unique=True
    )
    status: Mapped[RoomStatus] = mapped_column(
        Enum(RoomStatus), default=RoomStatus.active, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RoomMember(Base, TimestampMixin):
    __tablename__ = "room_members"
    __table_args__ = (UniqueConstraint("room_id", "user_id", name="uq_room_member"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ready_to_close: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
