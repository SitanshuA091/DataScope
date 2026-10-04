from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, JSON, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.dataset import DatasetVersion
    from app.db.models.tool_execution import ToolExecution
    from app.db.models.workspace import Workspace


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    workspace_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    dataset_version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    request_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    selected_tools_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        index=True,
        nullable=False,
    )

    results_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    error_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    timings_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    cache_key: Mapped[str | None] = mapped_column(
        String(255),
        index=True,
        nullable=True,
    )

    cache_hit: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    source_run_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    progress_stage: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    progress_percent: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
        nullable=False,
    )

    workspace: Mapped[Workspace] = relationship()
    dataset_version: Mapped[DatasetVersion] = relationship()
    tool_executions: Mapped[list[ToolExecution]] = relationship(
        back_populates="analysis_run",
        cascade="all, delete-orphan",
        order_by="ToolExecution.created_at",
    )
