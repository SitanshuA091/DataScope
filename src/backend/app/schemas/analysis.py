## Pydantic request/response models; never return raw ORM models.
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

AnalysisStatus = Literal["pending", "running", "completed", "failed", "cancelled"]
AnalysisExecutionMode = Literal["inline", "queued"]


class ToolSelection(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    arguments: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()


class AnalysisCreateRequest(BaseModel):
    tools: list[ToolSelection] = Field(min_length=1, max_length=20)
    include_plots: bool = False


class ToolExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_run_id: UUID
    tool_name: str
    arguments_json: dict[str, Any]
    status: str
    result_json: dict[str, Any] | None
    error_json: dict[str, Any] | None
    timings_json: dict[str, Any] | None
    cache_key: str | None = None
    cache_hit: bool = False
    source_execution_id: UUID | None = None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class AnalysisRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    dataset_version_id: UUID
    request_json: dict[str, Any]
    selected_tools_json: list[dict[str, Any]]
    status: str
    results_json: dict[str, Any] | None
    error_json: dict[str, Any] | None
    timings_json: dict[str, Any] | None
    cache_key: str | None = None
    cache_hit: bool = False
    source_run_id: UUID | None = None
    progress_stage: str | None = None
    progress_percent: int | None = None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime
    tool_executions: list[ToolExecutionResponse] = Field(default_factory=list)


class AnalysisRunSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: AnalysisStatus
    execution_mode: AnalysisExecutionMode
    dataset_version_id: UUID
    created_at: datetime


class AnalysisToolListResponse(BaseModel):
    tools: list[dict[str, Any]]
