from datetime import datetime, timedelta, timezone

from httpx import AsyncClient


async def test_create_recruitment(auth_client: AsyncClient):
    resp = await auth_client.post(
        "/api/recruitments",
        json={
            "game": "valorant",
            "region": "jp",
            "start_time": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["game"] == "valorant"
    assert data["region"] == "jp"
    assert data["status"] == "open"


async def test_create_recruitment_invalid_game(auth_client: AsyncClient):
    resp = await auth_client.post(
        "/api/recruitments",
        json={
            "game": "invalid_game",
            "region": "jp",
            "start_time": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert resp.status_code == 400


async def test_list_recruitments(auth_client: AsyncClient):
    await auth_client.post(
        "/api/recruitments",
        json={
            "game": "valorant",
            "region": "jp",
            "start_time": datetime.now(timezone.utc).isoformat(),
        },
    )
    resp = await auth_client.get("/api/recruitments")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1


async def test_cancel_recruitment(auth_client: AsyncClient):
    resp = await auth_client.post(
        "/api/recruitments",
        json={
            "game": "valorant",
            "region": "jp",
            "start_time": datetime.now(timezone.utc).isoformat(),
        },
    )
    rid = resp.json()["id"]
    resp = await auth_client.delete(f"/api/recruitments/{rid}")
    assert resp.status_code == 200


async def test_join_recruitment(auth_client: AsyncClient, second_auth_client: AsyncClient):
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
    assert resp.status_code == 200
    data = resp.json()
    assert data["detail"] == "Matched"
    assert "room_id" in data


async def test_cannot_join_own_recruitment(auth_client: AsyncClient):
    resp = await auth_client.post(
        "/api/recruitments",
        json={
            "game": "valorant",
            "region": "jp",
            "start_time": datetime.now(timezone.utc).isoformat(),
        },
    )
    rid = resp.json()["id"]
    resp = await auth_client.post(f"/api/recruitments/{rid}/join")
    assert resp.status_code == 400


async def test_duplicate_open_recruitment(auth_client: AsyncClient):
    await auth_client.post(
        "/api/recruitments",
        json={
            "game": "valorant",
            "region": "jp",
            "start_time": datetime.now(timezone.utc).isoformat(),
        },
    )
    resp = await auth_client.post(
        "/api/recruitments",
        json={
            "game": "apex_legends",
            "region": "jp",
            "start_time": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert resp.status_code == 400


async def test_create_recruitment_past_start_time(auth_client: AsyncClient):
    past_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    resp = await auth_client.post(
        "/api/recruitments",
        json={
            "game": "valorant",
            "region": "jp",
            "start_time": past_time,
        },
    )
    assert resp.status_code == 422
