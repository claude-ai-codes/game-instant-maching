from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.game import Game
from app.schemas.game import GameResponse

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("", response_model=list[GameResponse])
async def list_games(
    category: str | None = Query(None, max_length=30),
    platform: str | None = Query(None, max_length=20),
    q: str | None = Query(None, max_length=50),
    db: AsyncSession = Depends(get_db),
) -> list[GameResponse]:
    stmt = select(Game).where(Game.is_active.is_(True)).order_by(Game.name)

    if category:
        stmt = stmt.where(Game.category == category)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            Game.name.ilike(pattern) | Game.name_ja.ilike(pattern) | Game.slug.ilike(pattern)
        )

    result = await db.execute(stmt)
    games = [GameResponse.model_validate(g) for g in result.scalars().all()]

    # Filter by platform in Python (JSON column, cross-DB compatible)
    if platform:
        games = [g for g in games if g.platform_tags and platform in g.platform_tags]

    return games
