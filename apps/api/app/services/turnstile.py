import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def verify_turnstile_token(token: str, remote_ip: str | None = None) -> bool:
    """Verify a Cloudflare Turnstile CAPTCHA token.

    Returns True if verification passes or if Turnstile is not configured / in test env.
    """
    if settings.app_env == "test" or not settings.turnstile_secret_key:
        return True

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            payload: dict[str, str] = {
                "secret": settings.turnstile_secret_key,
                "response": token,
            }
            if remote_ip:
                payload["remoteip"] = remote_ip
            resp = await client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data=payload,
            )
            result = resp.json()
            return bool(result.get("success", False))
    except Exception:
        logger.exception("Turnstile verification request failed")
        return False
