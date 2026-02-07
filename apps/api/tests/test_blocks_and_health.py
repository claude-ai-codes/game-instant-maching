from httpx import AsyncClient


async def test_health(client: AsyncClient):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_delete_block_invalid_uuid(auth_client: AsyncClient):
    resp = await auth_client.delete("/api/blocks/not-a-uuid")
    assert resp.status_code == 422


async def test_block_and_unblock(auth_client: AsyncClient, second_auth_client: AsyncClient):
    me2 = await second_auth_client.get("/api/auth/me")
    user2_id = me2.json()["id"]

    resp = await auth_client.post("/api/blocks", json={"blocked_id": user2_id})
    assert resp.status_code == 201

    resp = await auth_client.get("/api/blocks")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await auth_client.delete(f"/api/blocks/{user2_id}")
    assert resp.status_code == 200

    resp = await auth_client.get("/api/blocks")
    assert resp.status_code == 200
    assert len(resp.json()) == 0
