from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class DatasetColumnSchema(BaseModel):
    name: str
    dtype: str
    nullable: bool
    missing_count: int


class DatasetVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    dataset_id: UUID
    version_number: int
    original_filename: str
    storage_key: str
    checksum: str
    file_size: int
    row_count: int
    column_count: int
    columns_schema: list[dict[str, Any]] = Field(
        validation_alias=AliasChoices("columns_schema", "schema_json"),
        serialization_alias="schema_json",
    )
    validation_status: str
    validation_error: str | None
    created_at: datetime


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    current_version_id: UUID | None
    created_at: datetime
    updated_at: datetime


class DatasetUploadResponse(BaseModel):
    dataset: DatasetResponse
    version: DatasetVersionResponse


class DatasetOverviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    dataset_id: UUID
    workspace_id: UUID
    dataset_name: str
    current_version_id: UUID
    version_number: int
    original_filename: str
    row_count: int
    column_count: int
    columns: list[str]
    columns_schema: list[dict[str, Any]] = Field(
        validation_alias=AliasChoices("columns_schema", "schema_json"),
        serialization_alias="schema_json",
    )
    validation_status: str
    validation_error: str | None
    created_at: datetime


class DatasetListItem(BaseModel):
    dataset: DatasetResponse
    current_version: DatasetVersionResponse | None = None


class DatasetListResponse(BaseModel):
    datasets: list[DatasetListItem] = Field(default_factory=list)
