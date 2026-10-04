from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.analysis_run import AnalysisRun
    from app.db.models.tool_execution import ToolExecution


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    analysis_run_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    tool_execution_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("tool_executions.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    artifact_type: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )

    storage_key: Mapped[str] = mapped_column(
        String(1024),
        index=True,
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False,
    )

    analysis_run: Mapped[AnalysisRun] = relationship()
    tool_execution: Mapped[ToolExecution | None] = relationship()
