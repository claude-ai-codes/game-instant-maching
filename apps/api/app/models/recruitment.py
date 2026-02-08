import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, new_uuid


class RecruitmentStatus(str, enum.Enum):
    open = "open"
    matched = "matched"
    cancelled = "cancelled"
    expired = "expired"


class PlayStyle(str, enum.Enum):
    casual = "casual"
    competitive = "competitive"
    beginner_welcome = "beginner_welcome"


class Recruitment(Base, TimestampMixin):
    __tablename__ = "recruitments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    game: Mapped[str] = mapped_column(String(50), nullable=False)
    region: Mapped[str] = mapped_column(String(20), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    desired_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    memo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    play_style: Mapped[PlayStyle | None] = mapped_column(Enum(PlayStyle), nullable=True)
    has_microphone: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[RecruitmentStatus] = mapped_column(
        Enum(RecruitmentStatus), default=RecruitmentStatus.open, nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
