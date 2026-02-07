import uuid

from pydantic import BaseModel


class BlockCreate(BaseModel):
    blocked_id: uuid.UUID


class BlockResponse(BaseModel):
    id: uuid.UUID
    blocker_id: uuid.UUID
    blocked_id: uuid.UUID

    model_config = {"from_attributes": True}
