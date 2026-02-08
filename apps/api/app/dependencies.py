import uuid

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.base import utcnow
from app.models.user import User


async def get_current_user(
    session_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    result = await db.execute(
        select(User).where(User.session_token == session_token, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    # Check ban
    if user.is_banned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is banned")

    # Check suspension
    if user.suspended_until and user.suspended_until > utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is temporarily suspended",
        )

    return user


async def get_optional_user(
    session_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not session_token:
        return None
    result = await db.execute(
        select(User).where(User.session_token == session_token, User.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def get_current_user_id(user: User = Depends(get_current_user)) -> uuid.UUID:
    return user.id
