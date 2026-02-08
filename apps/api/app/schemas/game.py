import uuid

from pydantic import BaseModel


class GameResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    name_ja: str | None
    category: str
    platform_tags: list[str] | None

    model_config = {"from_attributes": True}
