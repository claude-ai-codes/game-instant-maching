import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.auth import LoginRequest, UserResponse
from app.services.moderation import check_content
from app.services.turnstile import verify_turnstile_token
from app.utils.validators import sanitize_text

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/config")
async def auth_config() -> dict[str, str]:
    return {"turnstile_site_key": settings.turnstile_site_key}


@router.post("/login", response_model=UserResponse)
@limiter.limit("10/hour")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> User:
    nickname = sanitize_text(body.nickname)
    check_content(nickname, "nickname")

    # Verify Turnstile CAPTCHA when configured
    if settings.turnstile_secret_key and settings.app_env != "test":
        if not body.turnstile_token:
            raise HTTPException(status_code=400, detail="CAPTCHA verification required")
        remote_ip = request.client.host if request.client else None
        if not await verify_turnstile_token(body.turnstile_token, remote_ip):
            raise HTTPException(status_code=400, detail="CAPTCHA verification failed")

    token = secrets.token_hex(32)
    user = User(nickname=nickname, session_token=token)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.app_env not in ("development", "test"),
        path="/",
        max_age=86400,
    )
    return user


@router.post("/logout")
async def logout(
    response: Response,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    user.is_active = False
    await db.commit()
    response.delete_cookie("session_token", path="/")
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> User:
    return user
