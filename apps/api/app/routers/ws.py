import asyncio
import secrets
import time
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.dependencies import get_current_user
from app.models.user import User
from app.websocket import manager

router = APIRouter(prefix="/api/ws", tags=["websocket"])

# In-memory ticket store: ticket -> (user_id, expires_at)
_ws_tickets: dict[str, tuple[uuid.UUID, float]] = {}
_TICKET_TTL = 30  # seconds


def _cleanup_expired_tickets() -> None:
    now = time.time()
    expired = [k for k, (_, exp) in _ws_tickets.items() if exp < now]
    for k in expired:
        del _ws_tickets[k]


@router.post("/ticket")
async def create_ws_ticket(
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Issue a short-lived, single-use ticket for WebSocket authentication."""
    _cleanup_expired_tickets()
    ticket = secrets.token_urlsafe(32)
    _ws_tickets[ticket] = (user.id, time.time() + _TICKET_TTL)
    return {"ticket": ticket}


def _consume_ticket(ticket: str) -> uuid.UUID | None:
    """Validate and consume a WS ticket. Returns user_id or None."""
    _cleanup_expired_tickets()
    entry = _ws_tickets.pop(ticket, None)
    if entry is None:
        return None
    user_id, expires_at = entry
    if time.time() > expires_at:
        return None
    return user_id


@router.websocket("")
async def websocket_endpoint(ws: WebSocket):
    ticket = ws.query_params.get("ticket", "")
    user_id = _consume_ticket(ticket)
    if user_id is None:
        await ws.close(code=4001, reason="Authentication failed")
        return

    await ws.accept()
    await manager.connect(user_id, ws)
    try:
        while True:
            data = await asyncio.wait_for(ws.receive_text(), timeout=60)
            if data == "ping":
                await ws.send_text("pong")
    except (WebSocketDisconnect, asyncio.TimeoutError, Exception):
        pass
    finally:
        await manager.disconnect(user_id, ws)
