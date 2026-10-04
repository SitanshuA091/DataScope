from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.analysis import AnalysisRunResponse
from app.schemas.conversation import ConversationResponse, MessageResponse
from app.schemas.dataset import DatasetListItem


class WorkspaceCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class WorkspaceUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    last_activity_at: datetime
    deleted_at: datetime | None
    scheduled_deletion_at: datetime | None
    created_at: datetime
    updated_at: datetime


class WorkspaceListResponse(BaseModel):
    workspaces: list[WorkspaceResponse]


class WorkspaceConversationSummary(BaseModel):
    conversation: ConversationResponse
    messages: list[MessageResponse] = Field(default_factory=list)


class WorkspaceDetailResponse(BaseModel):
    workspace: WorkspaceResponse
    datasets: list[DatasetListItem] = Field(default_factory=list)
    recent_runs: list[AnalysisRunResponse] = Field(default_factory=list)
    conversations: list[WorkspaceConversationSummary] = Field(default_factory=list)
