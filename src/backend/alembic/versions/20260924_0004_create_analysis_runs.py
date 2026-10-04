"""create analysis runs

Revision ID: 20260924_0004
Revises: 20260923_0003
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260924_0004"
down_revision: str | Sequence[str] | None = "20260923_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("workspace_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("request_json", sa.JSON(), nullable=False),
        sa.Column("selected_tools_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("results_json", sa.JSON(), nullable=True),
        sa.Column("error_json", sa.JSON(), nullable=True),
        sa.Column("timings_json", sa.JSON(), nullable=True),
        sa.Column("cache_key", sa.String(length=255), nullable=True),
        sa.Column("cache_hit", sa.Boolean(), nullable=False),
        sa.Column("source_run_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("progress_stage", sa.String(length=255), nullable=True),
        sa.Column("progress_percent", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["dataset_version_id"], ["dataset_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_run_id"], ["analysis_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tool_executions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("arguments_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("error_json", sa.JSON(), nullable=True),
        sa.Column("timings_json", sa.JSON(), nullable=True),
        sa.Column("cache_key", sa.String(length=255), nullable=True),
        sa.Column("cache_hit", sa.Boolean(), nullable=False),
        sa.Column("source_execution_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_execution_id"], ["tool_executions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "artifacts",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("tool_execution_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"],
            ["analysis_runs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tool_execution_id"],
            ["tool_executions.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    for table, columns in {
        "analysis_runs": [
            "workspace_id",
            "dataset_version_id",
            "status",
            "cache_key",
            "source_run_id",
            "created_at",
            "started_at",
            "completed_at",
            "updated_at",
        ],
        "tool_executions": [
            "analysis_run_id",
            "tool_name",
            "status",
            "cache_key",
            "source_execution_id",
            "created_at",
            "started_at",
            "completed_at",
        ],
        "artifacts": [
            "analysis_run_id",
            "tool_execution_id",
            "artifact_type",
            "storage_key",
            "created_at",
        ],
    }.items():
        for column in columns:
            op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def downgrade() -> None:
    for table, columns in {
        "artifacts": [
            "created_at",
            "storage_key",
            "artifact_type",
            "tool_execution_id",
            "analysis_run_id",
        ],
        "tool_executions": [
            "completed_at",
            "started_at",
            "created_at",
            "source_execution_id",
            "cache_key",
            "status",
            "tool_name",
            "analysis_run_id",
        ],
        "analysis_runs": [
            "updated_at",
            "completed_at",
            "started_at",
            "created_at",
            "source_run_id",
            "cache_key",
            "status",
            "dataset_version_id",
            "workspace_id",
        ],
    }.items():
        for column in columns:
            op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)

    op.drop_table("artifacts")
    op.drop_table("tool_executions")
    op.drop_table("analysis_runs")
