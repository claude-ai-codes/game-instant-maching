"""Tests for authorization/behavior fixes (fix-instructions.md)."""

import uuid
from datetime import datetime, timezone

from httpx import AsyncClient

# --- Fix 2: Report endpoint validation ---


async def test_report_nonexistent_user(auth_client: AsyncClient):
    fake_id = str(uuid.uuid4())
    resp = await auth_client.post(
        "/api/reports",
        json={"reported_id": fake_id, "reason": "spam"},
    )
    assert resp.status_code == 404
    assert "Reported user not found" in resp.json()["detail"]


async def test_report_nonexistent_room(
    auth_client: AsyncClient, second_auth_client: AsyncClient
):
    me2 = await second_auth_client.get("/api/auth/me")
    user2_id = me2.json()["id"]

    fake_room_id = str(uuid.uuid4())
    resp = await auth_client.post(
        "/api/reports",
        json={"reported_id": user2_id, "room_id": fake_room_id, "reason": "spam"},
    )
    assert resp.status_code == 404
    assert "Room not found" in resp.json()["detail"]


async def test_report_non_member_room(
    auth_client: AsyncClient, second_auth_client: AsyncClient
):
    """Create a room between user1 and user2, then try to report from a third user."""
    # Create recruitment and join to make a room
    now = datetime.now(timezone.utc).isoformat()
    resp = await auth_client.post(
        "/api/recruitments",
        json={"game": "valorant", "region": "jp", "start_time": now},
    )
    rid = resp.json()["id"]
    join_resp = await second_auth_client.post(f"/api/recruitments/{rid}/join")
    room_id = join_resp.json()["room_id"]

    me2 = await second_auth_client.get("/api/auth/me")
    user2_id = me2.json()["id"]

    # Create a third user
    from httpx import ASGITransport
    from httpx import AsyncClient as AC

    from app.main import app

    transport = ASGITransport(app=app)
    async with AC(transport=transport, base_url="http://test") as third:
        await third.post("/api/auth/login", json={"nickname": "thirduser"})
        # Third user tries to report user2 in a room they're not a member of
        resp = await third.post(
            "/api/reports",
            json={"reported_id": user2_id, "room_id": room_id, "reason": "spam"},
        )
        assert resp.status_code == 403
        assert "not a member" in resp.json()["detail"]


# --- Fix 3: Block nonexistent user ---


async def test_block_nonexistent_user(auth_client: AsyncClient):
    fake_id = str(uuid.uuid4())
    resp = await auth_client.post("/api/blocks", json={"blocked_id": fake_id})
    assert resp.status_code == 404
    assert "User not found" in resp.json()["detail"]


# --- Fix 1: Mutual close ---


async def test_single_close_is_pending(
    auth_client: AsyncClient, second_auth_client: AsyncClient
):
    now = datetime.now(timezone.utc).isoformat()
    resp = await auth_client.post(
        "/api/recruitments",
        json={"game": "valorant", "region": "jp", "start_time": now},
    )
    rid = resp.json()["id"]
    join_resp = await second_auth_client.post(f"/api/recruitments/{rid}/join")
    room_id = join_resp.json()["room_id"]

    # User1 closes — should be pending
    resp = await auth_client.post(f"/api/rooms/{room_id}/close")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending_close"

    # Room should still be active
    room_resp = await auth_client.get(f"/api/rooms/{room_id}")
    assert room_resp.json()["status"] == "active"


async def test_double_close_rejected(
    auth_client: AsyncClient, second_auth_client: AsyncClient
):
    now = datetime.now(timezone.utc).isoformat()
    resp = await auth_client.post(
        "/api/recruitments",
        json={"game": "valorant", "region": "jp", "start_time": now},
    )
    rid = resp.json()["id"]
    join_resp = await second_auth_client.post(f"/api/recruitments/{rid}/join")
    room_id = join_resp.json()["room_id"]

    # User1 closes
    await auth_client.post(f"/api/rooms/{room_id}/close")
    # User1 tries again
    resp = await auth_client.post(f"/api/rooms/{room_id}/close")
    assert resp.status_code == 400
    assert "already requested close" in resp.json()["detail"]


async def test_mutual_close_completes(
    auth_client: AsyncClient, second_auth_client: AsyncClient
):
    now = datetime.now(timezone.utc).isoformat()
    resp = await auth_client.post(
        "/api/recruitments",
        json={"game": "valorant", "region": "jp", "start_time": now},
    )
    rid = resp.json()["id"]
    join_resp = await second_auth_client.post(f"/api/recruitments/{rid}/join")
    room_id = join_resp.json()["room_id"]

    # User1 closes
    resp1 = await auth_client.post(f"/api/rooms/{room_id}/close")
    assert resp1.json()["status"] == "pending_close"

    # User2 closes — should complete
    resp2 = await second_auth_client.post(f"/api/rooms/{room_id}/close")
    assert resp2.json()["status"] == "closed"

    # Room should be closed
    room_resp = await auth_client.get(f"/api/rooms/{room_id}")
    assert room_resp.json()["status"] == "closed"


# --- Fix 5: Block hides recruitments ---


async def test_blocked_user_recruitment_hidden(
    auth_client: AsyncClient, second_auth_client: AsyncClient
):
    me2 = await second_auth_client.get("/api/auth/me")
    user2_id = me2.json()["id"]

    # User2 creates a recruitment
    now = datetime.now(timezone.utc).isoformat()
    await second_auth_client.post(
        "/api/recruitments",
        json={"game": "valorant", "region": "jp", "start_time": now},
    )

    # User1 can see it
    resp = await auth_client.get("/api/recruitments")
    ids_before = [r["user_id"] for r in resp.json()]
    assert user2_id in ids_before

    # User1 blocks User2
    await auth_client.post("/api/blocks", json={"blocked_id": user2_id})

    # User1 can no longer see User2's recruitment
    resp = await auth_client.get("/api/recruitments")
    ids_after = [r["user_id"] for r in resp.json()]
    assert user2_id not in ids_after
