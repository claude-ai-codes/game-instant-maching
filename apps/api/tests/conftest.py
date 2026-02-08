import asyncio
import os
from collections.abc import AsyncGenerator

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import app
from app.models.base import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


async def _seed_games(session: AsyncSession):
    """Seed the games table with test data matching packages/shared/games.json slugs."""
    from app.models.game import Game

    games_data = [
        ("valorant", "VALORANT", "fps"),
        ("league_of_legends", "League of Legends", "moba"),
        ("apex_legends", "Apex Legends", "fps"),
        ("overwatch2", "Overwatch 2", "fps"),
        ("fortnite", "Fortnite", "fps"),
        ("splatoon3", "Splatoon 3", "tps"),
        ("street_fighter6", "Street Fighter 6", "fighting"),
        ("pokemon_unite", "Pokemon UNITE", "moba"),
        ("marvel_rivals", "Marvel Rivals", "fps"),
        ("other", "Other", "other"),
    ]
    for slug, name, category in games_data:
        session.add(Game(slug=slug, name=name, category=category, is_active=True))
    await session.commit()


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        await _seed_games(session)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    resp = await client.post("/api/auth/login", json={"nickname": "testuser"})
    assert resp.status_code == 200
    return client


@pytest.fixture
async def second_auth_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post("/api/auth/login", json={"nickname": "testuser2"})
        assert resp.status_code == 200
        yield c
