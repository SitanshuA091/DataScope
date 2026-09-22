"""create workspaces

Revision ID: 20260922_0001
Revises:
Create Date: 2026-09-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260922_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column(
            "last_activity_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "scheduled_deletion_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_workspaces_created_at"),
        "workspaces",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workspaces_deleted_at"),
        "workspaces",
        ["deleted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workspaces_last_activity_at"),
        "workspaces",
        ["last_activity_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workspaces_scheduled_deletion_at"),
        "workspaces",
        ["scheduled_deletion_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workspaces_title"),
        "workspaces",
        ["title"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workspaces_updated_at"),
        "workspaces",
        ["updated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_workspaces_user_id"),
        "workspaces",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_workspaces_user_id"), table_name="workspaces")
    op.drop_index(op.f("ix_workspaces_updated_at"), table_name="workspaces")
    op.drop_index(op.f("ix_workspaces_title"), table_name="workspaces")
    op.drop_index(
        op.f("ix_workspaces_scheduled_deletion_at"),
        table_name="workspaces",
    )
    op.drop_index(
        op.f("ix_workspaces_last_activity_at"),
        table_name="workspaces",
    )
    op.drop_index(op.f("ix_workspaces_deleted_at"), table_name="workspaces")
    op.drop_index(op.f("ix_workspaces_created_at"), table_name="workspaces")
    op.drop_table("workspaces")
