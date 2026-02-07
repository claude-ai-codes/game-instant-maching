from datetime import datetime, timezone

from httpx import AsyncClient


async def _create_room(
    auth_client: AsyncClient, second_auth_client: AsyncClient
) -> tuple[str, str, str]:
    """Create a matched room, return (room_id, user1_id, user2_id)."""
    me1 = await auth_client.get("/api/auth/me")
    user1_id = me1.json()["id"]
    me2 = await second_auth_client.get("/api/auth/me")
    user2_id = me2.json()["id"]

    resp = await auth_client.post(
        "/api/recruitments",
        json={
            "game": "valorant",
            "region": "jp",
            "start_time": datetime.now(timezone.utc).isoformat(),
        },
    )
    rid = resp.json()["id"]

    resp = await second_auth_client.post(f"/api/recruitments/{rid}/join")
    room_id = resp.json()["room_id"]
    return room_id, user1_id, user2_id


async def test_get_room(auth_client: AsyncClient, second_auth_client: AsyncClient):
    room_id, _, _ = await _create_room(auth_client, second_auth_client)
    resp = await auth_client.get(f"/api/rooms/{room_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "active"
    assert len(data["members"]) == 2


async def test_send_message(auth_client: AsyncClient, second_auth_client: AsyncClient):
    room_id, _, _ = await _create_room(auth_client, second_auth_client)
    resp = await auth_client.post(
        f"/api/rooms/{room_id}/messages", json={"content": "Hello!"}
    )
    assert resp.status_code == 201
    assert resp.json()["content"] == "Hello!"


async def test_get_messages(auth_client: AsyncClient, second_auth_client: AsyncClient):
    room_id, _, _ = await _create_room(auth_client, second_auth_client)
    await auth_client.post(f"/api/rooms/{room_id}/messages", json={"content": "msg1"})
    await second_auth_client.post(f"/api/rooms/{room_id}/messages", json={"content": "msg2"})
    resp = await auth_client.get(f"/api/rooms/{room_id}/messages")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_close_room(auth_client: AsyncClient, second_auth_client: AsyncClient):
    room_id, _, _ = await _create_room(auth_client, second_auth_client)
    resp = await auth_client.post(f"/api/rooms/{room_id}/close")
    assert resp.status_code == 200

    resp = await auth_client.get(f"/api/rooms/{room_id}")
    assert resp.json()["status"] == "closed"


async def test_feedback(auth_client: AsyncClient, second_auth_client: AsyncClient):
    room_id, user1_id, user2_id = await _create_room(auth_client, second_auth_client)
    await auth_client.post(f"/api/rooms/{room_id}/close")

    resp = await auth_client.post(
        f"/api/rooms/{room_id}/feedback",
        json={"to_user_id": user2_id, "rating": "thumbs_up"},
    )
    assert resp.status_code == 201

    # Duplicate feedback
    resp = await auth_client.post(
        f"/api/rooms/{room_id}/feedback",
        json={"to_user_id": user2_id, "rating": "thumbs_down"},
    )
    assert resp.status_code == 409


async def test_message_ng_word(auth_client: AsyncClient, second_auth_client: AsyncClient):
    room_id, _, _ = await _create_room(auth_client, second_auth_client)
    resp = await auth_client.post(
        f"/api/rooms/{room_id}/messages", json={"content": "fuck you"}
    )
    assert resp.status_code == 400


async def test_message_url_rejected(auth_client: AsyncClient, second_auth_client: AsyncClient):
    room_id, _, _ = await _create_room(auth_client, second_auth_client)
    resp = await auth_client.post(
        f"/api/rooms/{room_id}/messages", json={"content": "go to https://evil.com"}
    )
    assert resp.status_code == 400


async def test_cannot_message_closed_room(
    auth_client: AsyncClient, second_auth_client: AsyncClient
):
    room_id, _, _ = await _create_room(auth_client, second_auth_client)
    await auth_client.post(f"/api/rooms/{room_id}/close")
    resp = await auth_client.post(f"/api/rooms/{room_id}/messages", json={"content": "hi"})
    assert resp.status_code == 400
