from httpx import AsyncClient


async def test_login(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={"nickname": "player1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["nickname"] == "player1"
    assert "id" in data
    assert "session_token" in resp.cookies


async def test_login_invalid_nickname_too_short(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={"nickname": "a"})
    assert resp.status_code == 422


async def test_login_invalid_nickname_too_long(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={"nickname": "a" * 21})
    assert resp.status_code == 422


async def test_me(auth_client: AsyncClient):
    resp = await auth_client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["nickname"] == "testuser"


async def test_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_logout(auth_client: AsyncClient):
    resp = await auth_client.post("/api/auth/logout")
    assert resp.status_code == 200


async def test_login_ng_word(client: AsyncClient):
    resp = await client.post("/api/auth/login", json={"nickname": "fuck"})
    assert resp.status_code == 400
