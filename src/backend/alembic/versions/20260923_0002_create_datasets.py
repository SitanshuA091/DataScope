"""create datasets

Revision ID: 20260923_0002
Revises: 20260922_0001
Create Date: 2026-09-23
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260923_0002"
down_revision: str | Sequence[str] | None = "20260922_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("workspace_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("current_version_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "dataset_versions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("dataset_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("column_count", sa.Integer(), nullable=False),
        sa.Column("schema_json", sa.JSON(), nullable=False),
        sa.Column("validation_status", sa.String(length=32), nullable=False),
        sa.Column("validation_error", sa.String(length=2048), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_id", "version_number"),
    )
    op.create_foreign_key(
        "fk_datasets_current_version_id_dataset_versions",
        "datasets",
        "dataset_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index(op.f("ix_datasets_created_at"), "datasets", ["created_at"])
    op.create_index(
        op.f("ix_datasets_current_version_id"),
        "datasets",
        ["current_version_id"],
    )
    op.create_index(op.f("ix_datasets_name"), "datasets", ["name"])
    op.create_index(op.f("ix_datasets_updated_at"), "datasets", ["updated_at"])
    op.create_index(
        op.f("ix_datasets_workspace_id"),
        "datasets",
        ["workspace_id"],
    )
    op.create_index(
        op.f("ix_dataset_versions_checksum"),
        "dataset_versions",
        ["checksum"],
    )
    op.create_index(
        op.f("ix_dataset_versions_created_at"),
        "dataset_versions",
        ["created_at"],
    )
    op.create_index(
        op.f("ix_dataset_versions_dataset_id"),
        "dataset_versions",
        ["dataset_id"],
    )
    op.create_index(
        op.f("ix_dataset_versions_storage_key"),
        "dataset_versions",
        ["storage_key"],
        unique=True,
    )
    op.create_index(
        op.f("ix_dataset_versions_validation_status"),
        "dataset_versions",
        ["validation_status"],
    )
    op.create_index(
        op.f("ix_dataset_versions_version_number"),
        "dataset_versions",
        ["version_number"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_dataset_versions_version_number"),
        table_name="dataset_versions",
    )
    op.drop_index(
        op.f("ix_dataset_versions_validation_status"),
        table_name="dataset_versions",
    )
    op.drop_index(
        op.f("ix_dataset_versions_storage_key"),
        table_name="dataset_versions",
    )
    op.drop_index(
        op.f("ix_dataset_versions_dataset_id"),
        table_name="dataset_versions",
    )
    op.drop_index(
        op.f("ix_dataset_versions_created_at"),
        table_name="dataset_versions",
    )
    op.drop_index(
        op.f("ix_dataset_versions_checksum"),
        table_name="dataset_versions",
    )
    op.drop_index(op.f("ix_datasets_workspace_id"), table_name="datasets")
    op.drop_index(op.f("ix_datasets_updated_at"), table_name="datasets")
    op.drop_index(op.f("ix_datasets_name"), table_name="datasets")
    op.drop_index(
        op.f("ix_datasets_current_version_id"),
        table_name="datasets",
    )
    op.drop_index(op.f("ix_datasets_created_at"), table_name="datasets")
    op.drop_constraint(
        "fk_datasets_current_version_id_dataset_versions",
        "datasets",
        type_="foreignkey",
    )
    op.drop_table("dataset_versions")
    op.drop_table("datasets")
