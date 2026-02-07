"""Tests for WebSocket ConnectionManager, ticket auth, and WS connection."""

import uuid

import pytest
from httpx import AsyncClient
from starlette.testclient import TestClient

from app.main import app
from app.routers.ws import _consume_ticket
from app.websocket import ConnectionManager

# --- ConnectionManager unit tests ---


async def test_manager_connect_disconnect():
    mgr = ConnectionManager()
    user_id = uuid.uuid4()

    class FakeWS:
        sent: list = []

        async def send_json(self, data):
            self.sent.append(data)

    ws = FakeWS()
    await mgr.connect(user_id, ws)
    assert user_id in mgr._connections
    assert ws in mgr._connections[user_id]
    assert ws in mgr._lobby

    await mgr.disconnect(user_id, ws)
    assert user_id not in mgr._connections
    assert ws not in mgr._lobby


async def test_manager_send_to_user():
    mgr = ConnectionManager()
    user_id = uuid.uuid4()

    class FakeWS:
        sent: list

        def __init__(self):
            self.sent = []

        async def send_json(self, data):
            self.sent.append(data)

    ws = FakeWS()
    await mgr.connect(user_id, ws)
    await mgr.send_to_user(user_id, {"type": "test", "data": {}})
    assert len(ws.sent) == 1
    assert ws.sent[0]["type"] == "test"

    await mgr.disconnect(user_id, ws)


async def test_manager_send_to_unknown_user():
    mgr = ConnectionManager()
    # Should not raise
    await mgr.send_to_user(uuid.uuid4(), {"type": "test"})


async def test_manager_stale_connection_cleanup():
    mgr = ConnectionManager()
    user_id = uuid.uuid4()

    class StaleWS:
        async def send_json(self, data):
            raise ConnectionError("gone")

    ws = StaleWS()
    await mgr.connect(user_id, ws)
    await mgr.send_to_user(user_id, {"type": "test"})
    # Stale connection should be cleaned up
    assert user_id not in mgr._connections
    assert ws not in mgr._lobby


async def test_manager_broadcast_to_lobby():
    mgr = ConnectionManager()

    class FakeWS:
        sent: list

        def __init__(self):
            self.sent = []

        async def send_json(self, data):
            self.sent.append(data)

    ws1 = FakeWS()
    ws2 = FakeWS()
    await mgr.connect(uuid.uuid4(), ws1)
    await mgr.connect(uuid.uuid4(), ws2)

    await mgr.broadcast_to_lobby({"type": "lobby_update"})
    assert len(ws1.sent) == 1
    assert len(ws2.sent) == 1


async def test_manager_send_to_users():
    mgr = ConnectionManager()
    uid1 = uuid.uuid4()
    uid2 = uuid.uuid4()

    class FakeWS:
        sent: list

        def __init__(self):
            self.sent = []

        async def send_json(self, data):
            self.sent.append(data)

    ws1 = FakeWS()
    ws2 = FakeWS()
    await mgr.connect(uid1, ws1)
    await mgr.connect(uid2, ws2)

    await mgr.send_to_users([uid1, uid2], {"type": "multi"})
    assert len(ws1.sent) == 1
    assert len(ws2.sent) == 1


# --- WS ticket tests ---


async def test_ws_ticket_endpoint(auth_client: AsyncClient):
    resp = await auth_client.post("/api/ws/ticket")
    assert resp.status_code == 200
    data = resp.json()
    assert "ticket" in data
    assert len(data["ticket"]) > 0


async def test_ws_ticket_requires_auth(client: AsyncClient):
    resp = await client.post("/api/ws/ticket")
    assert resp.status_code == 401


async def test_ws_ticket_single_use(auth_client: AsyncClient):
    resp = await auth_client.post("/api/ws/ticket")
    ticket = resp.json()["ticket"]
    # First consume should succeed
    user_id = _consume_ticket(ticket)
    assert user_id is not None
    # Second consume should fail (single-use)
    assert _consume_ticket(ticket) is None


# --- WebSocket connection integration test ---


def test_ws_connection_with_invalid_ticket():
    """WebSocket connection with invalid ticket should close with 4001."""
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect("/api/ws?ticket=invalid"):
            pass


def test_ws_connection_with_valid_ticket():
    """WebSocket connection with valid ticket should succeed."""
    client = TestClient(app)

    # Login to get a session
    resp = client.post("/api/auth/login", json={"nickname": "wsuser"})
    assert resp.status_code == 200

    # Get a ticket
    resp = client.post("/api/ws/ticket")
    assert resp.status_code == 200
    ticket = resp.json()["ticket"]

    # Connect via WebSocket
    with client.websocket_connect(f"/api/ws?ticket={ticket}") as ws:
        ws.send_text("ping")
        data = ws.receive_text()
        assert data == "pong"
