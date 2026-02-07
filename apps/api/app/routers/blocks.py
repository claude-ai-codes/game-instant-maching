from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.block import Block
from app.models.user import User
from app.schemas.block import BlockCreate, BlockResponse

router = APIRouter(prefix="/api/blocks", tags=["blocks"])


@router.get("", response_model=list[BlockResponse])
async def list_blocks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Block]:
    result = await db.execute(select(Block).where(Block.blocker_id == user.id))
    return list(result.scalars().all())


@router.post("", response_model=BlockResponse, status_code=status.HTTP_201_CREATED)
async def create_block(
    body: BlockCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Block:
    if body.blocked_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")

    existing = await db.execute(
        select(Block).where(Block.blocker_id == user.id, Block.blocked_id == body.blocked_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already blocked")

    block = Block(blocker_id=user.id, blocked_id=body.blocked_id)
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return block


@router.delete("/{blocked_id}")
async def delete_block(
    blocked_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    result = await db.execute(
        select(Block).where(Block.blocker_id == user.id, Block.blocked_id == blocked_id)
    )
    block = result.scalar_one_or_none()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    await db.delete(block)
    await db.commit()
    return {"detail": "Unblocked"}
