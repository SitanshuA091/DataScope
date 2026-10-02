"""Strict contracts for agent planning and interpretation."""
from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

AgentToolName = Literal["high_level", "column", "relationships", "quality"]


class DatasetColumn(BaseModel):
    name: str
    dtype: str
    nullable: bool | None = None
    missing_count: int | None = None


class DatasetContext(BaseModel):
    dataset_id: UUID
    dataset_version_id: UUID
    row_count: int
    column_count: int
    columns: list[DatasetColumn]
    active_columns: list[str] = Field(default_factory=list)

    @property
    def column_names(self) -> set[str]:
        return {column.name for column in self.columns}


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)


class ToolCallPlan(BaseModel):
    name: AgentToolName
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("arguments")
    @classmethod
    def normalize_arguments(cls, value: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(value)
        columns = normalized.get("columns")
        if columns is not None:
            if not isinstance(columns, list):
                raise ValueError("columns must be a list of column names")
            normalized["columns"] = [
                str(column).strip()
                for column in columns
                if str(column).strip()
            ]
        return normalized


class AgentPlan(BaseModel):
    intent: str = Field(min_length=1, max_length=500)
    requires_clarification: bool = False
    clarification_question: str | None = Field(default=None, max_length=500)
    tools: list[ToolCallPlan] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def validate_clarification(self) -> AgentPlan:
        if self.requires_clarification and not self.clarification_question:
            raise ValueError("clarification_question is required")
        if not self.requires_clarification and not self.tools:
            raise ValueError("at least one tool is required")
        return self


class AnalysisInterpretation(BaseModel):
    answer: str = Field(min_length=1)
    key_findings: list[str] = Field(default_factory=list, max_length=10)
    limitations: list[str] = Field(default_factory=list, max_length=10)
    follow_up_questions: list[str] = Field(default_factory=list, max_length=5)


class AgentRunResult(BaseModel):
    dataset_id: UUID
    dataset_version_id: UUID
    question: str
    plan: AgentPlan
    analysis_run_id: UUID | None = None
    interpretation: AnalysisInterpretation | None = None
    assistant_message: str | None = None
