## Pydantic request/response models; never return raw ORM models.
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str | None
    avatar_url: str | None
    created_at: datetime
