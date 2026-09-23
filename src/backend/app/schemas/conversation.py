from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

MessageRole = Literal["user", "assistant", "system"]


class ConversationOpenRequest(BaseModel):
    active_columns: list[str] = Field(default_factory=list, max_length=100)


class ConversationColumnsUpdate(BaseModel):
    active_columns: list[str] = Field(default_factory=list, max_length=100)


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    dataset_version_id: UUID
    active_columns_json: list[str]
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    role: MessageRole
    content: str = Field(min_length=1, max_length=20_000)
    analysis_run_id: UUID | None = None


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    analysis_run_id: UUID | None
    created_at: datetime


class MessageListResponse(BaseModel):
    conversation: ConversationResponse
    messages: list[MessageResponse] = Field(default_factory=list)


class QuestionUsageResponse(BaseModel):
    conversation_id: UUID
    used: int
    limit: int
    remaining: int
