"""Tests for Turnstile CAPTCHA verification and auth config endpoint."""

from httpx import AsyncClient

from app.services.turnstile import verify_turnstile_token


async def test_turnstile_returns_true_in_test_env():
    """In test env, Turnstile verification should always pass."""
    result = await verify_turnstile_token("any-token", "127.0.0.1")
    assert result is True


async def test_turnstile_returns_true_with_empty_token():
    """In test env, even empty token should pass."""
    result = await verify_turnstile_token("", None)
    assert result is True


async def test_auth_config_endpoint(client: AsyncClient):
    resp = await client.get("/api/auth/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "turnstile_site_key" in data
    # Default is empty in test env
    assert data["turnstile_site_key"] == ""


async def test_login_with_turnstile_token(client: AsyncClient):
    """Login should accept turnstile_token field without errors in test env."""
    resp = await client.post(
        "/api/auth/login",
        json={"nickname": "captchauser", "turnstile_token": "test-token"},
    )
    assert resp.status_code == 200
    assert resp.json()["nickname"] == "captchauser"


async def test_login_without_turnstile_token(client: AsyncClient):
    """Login should work without turnstile_token (backward compatible)."""
    resp = await client.post(
        "/api/auth/login",
        json={"nickname": "notoken"},
    )
    assert resp.status_code == 200
    assert resp.json()["nickname"] == "notoken"
