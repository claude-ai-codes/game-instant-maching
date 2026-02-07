import asyncio
import logging
import uuid
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections per user, with lobby broadcast support."""

    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, set[WebSocket]] = {}
        self._lobby: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, user_id: uuid.UUID, ws: WebSocket) -> None:
        async with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = set()
            self._connections[user_id].add(ws)
            self._lobby.add(ws)

    async def disconnect(self, user_id: uuid.UUID, ws: WebSocket) -> None:
        async with self._lock:
            conns = self._connections.get(user_id)
            if conns:
                conns.discard(ws)
                if not conns:
                    del self._connections[user_id]
            self._lobby.discard(ws)

    async def send_to_user(self, user_id: uuid.UUID, data: dict[str, Any]) -> None:
        async with self._lock:
            conns = self._connections.get(user_id)
            if not conns:
                return
            stale: list[WebSocket] = []
            for ws in conns:
                try:
                    await ws.send_json(data)
                except Exception:
                    stale.append(ws)
            for ws in stale:
                conns.discard(ws)
                self._lobby.discard(ws)
            if not conns:
                del self._connections[user_id]

    async def send_to_users(self, user_ids: list[uuid.UUID], data: dict[str, Any]) -> None:
        for uid in user_ids:
            await self.send_to_user(uid, data)

    async def broadcast_to_lobby(self, data: dict[str, Any]) -> None:
        async with self._lock:
            stale: list[WebSocket] = []
            for ws in self._lobby:
                try:
                    await ws.send_json(data)
                except Exception:
                    stale.append(ws)
            for ws in stale:
                self._lobby.discard(ws)


manager = ConnectionManager()
