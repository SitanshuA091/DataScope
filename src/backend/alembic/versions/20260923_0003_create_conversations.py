"""create conversations

Revision ID: 20260923_0003
Revises: 20260923_0002
Create Date: 2026-09-23
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260923_0003"
down_revision: str | Sequence[str] | None = "20260923_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("workspace_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("dataset_version_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("active_columns_json", sa.JSON(), nullable=False),
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
            ["dataset_version_id"],
            ["dataset_versions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "dataset_version_id",
            name="uq_conversations_workspace_dataset_version",
        ),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("conversation_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_conversations_created_at"),
        "conversations",
        ["created_at"],
    )
    op.create_index(
        op.f("ix_conversations_dataset_version_id"),
        "conversations",
        ["dataset_version_id"],
    )
    op.create_index(
        op.f("ix_conversations_updated_at"),
        "conversations",
        ["updated_at"],
    )
    op.create_index(
        op.f("ix_conversations_workspace_id"),
        "conversations",
        ["workspace_id"],
    )
    op.create_index(
        op.f("ix_messages_analysis_run_id"),
        "messages",
        ["analysis_run_id"],
    )
    op.create_index(
        op.f("ix_messages_conversation_id"),
        "messages",
        ["conversation_id"],
    )
    op.create_index(
        op.f("ix_messages_created_at"),
        "messages",
        ["created_at"],
    )
    op.create_index(op.f("ix_messages_role"), "messages", ["role"])


def downgrade() -> None:
    op.drop_index(op.f("ix_messages_role"), table_name="messages")
    op.drop_index(op.f("ix_messages_created_at"), table_name="messages")
    op.drop_index(op.f("ix_messages_conversation_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_analysis_run_id"), table_name="messages")
    op.drop_index(
        op.f("ix_conversations_workspace_id"),
        table_name="conversations",
    )
    op.drop_index(
        op.f("ix_conversations_updated_at"),
        table_name="conversations",
    )
    op.drop_index(
        op.f("ix_conversations_dataset_version_id"),
        table_name="conversations",
    )
    op.drop_index(
        op.f("ix_conversations_created_at"),
        table_name="conversations",
    )
    op.drop_table("messages")
    op.drop_table("conversations")
