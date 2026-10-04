## Pydantic request/response models; never return raw ORM models.
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AnalysisRunHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    dataset_version_id: UUID
    status: str
    selected_tools_json: list[dict[str, Any]]
    error_json: dict[str, Any] | None
    progress_stage: str | None = None
    progress_percent: int | None = None
    cache_hit: bool = False
    source_run_id: UUID | None = None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime


class AnalysisRunHistoryResponse(BaseModel):
    analysis_runs: list[AnalysisRunHistoryItem]


class AnalysisArtifactResponse(BaseModel):
    artifact_type: str
    storage_key: str | None = None
    mime_type: str | None = None
    tool_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalysisArtifactListResponse(BaseModel):
    artifacts: list[AnalysisArtifactResponse]


class AnalysisRunResultsResponse(BaseModel):
    run_id: UUID
    status: str
    metrics: dict[str, Any]
    explanation: dict[str, Any] | None = None
    artifacts: list[AnalysisArtifactResponse]
    errors: dict[str, Any] | None = None
    cache_hit: bool = False
    source_run_id: UUID | None = None
