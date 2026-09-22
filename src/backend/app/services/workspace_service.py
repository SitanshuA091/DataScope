from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.workspace import Workspace

DEFAULT_WORKSPACE_TITLE = "Untitled workspace"
WORKSPACE_RECOVERY_DAYS = 7


def _normalize_title(title: str | None) -> str:
    normalized = (title or DEFAULT_WORKSPACE_TITLE).strip()
    return normalized or DEFAULT_WORKSPACE_TITLE


def create_workspace(
    db: Session,
    user_id: UUID,
    title: str | None = None,
) -> Workspace:
    now = datetime.now(UTC)
    workspace = Workspace(
        user_id=user_id,
        title=_normalize_title(title),
        last_activity_at=now,
    )

    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


def list_workspaces(
    db: Session,
    user_id: UUID,
) -> list[Workspace]:
    return list(
        db.scalars(
            select(Workspace)
            .where(
                Workspace.user_id == user_id,
                Workspace.deleted_at.is_(None),
                Workspace.scheduled_deletion_at.is_(None),
            )
            .order_by(
                Workspace.last_activity_at.desc(),
                Workspace.created_at.desc(),
            )
        )
    )


def get_workspace(
    db: Session,
    user_id: UUID,
    workspace_id: UUID,
    *,
    include_deleted: bool = False,
) -> Workspace:
    conditions = [
        Workspace.id == workspace_id,
        Workspace.user_id == user_id,
    ]

    if not include_deleted:
        conditions.extend(
            [
                Workspace.deleted_at.is_(None),
                Workspace.scheduled_deletion_at.is_(None),
            ]
        )

    workspace = db.scalar(select(Workspace).where(*conditions))

    if workspace is None:
        raise NotFoundError("Workspace was not found.")

    return workspace


def rename_workspace(
    db: Session,
    user_id: UUID,
    workspace_id: UUID,
    title: str,
) -> Workspace:
    workspace = get_workspace(
        db=db,
        user_id=user_id,
        workspace_id=workspace_id,
    )

    workspace.title = _normalize_title(title)
    workspace.last_activity_at = datetime.now(UTC)

    db.commit()
    db.refresh(workspace)
    return workspace


def touch_workspace(
    db: Session,
    user_id: UUID,
    workspace_id: UUID,
) -> Workspace:
    workspace = get_workspace(
        db=db,
        user_id=user_id,
        workspace_id=workspace_id,
    )

    workspace.last_activity_at = datetime.now(UTC)

    db.commit()
    db.refresh(workspace)
    return workspace


def schedule_workspace_deletion(
    db: Session,
    user_id: UUID,
    workspace_id: UUID,
) -> Workspace:
    workspace = get_workspace(
        db=db,
        user_id=user_id,
        workspace_id=workspace_id,
    )

    now = datetime.now(UTC)
    workspace.deleted_at = now
    workspace.scheduled_deletion_at = now + timedelta(days=WORKSPACE_RECOVERY_DAYS)

    db.commit()
    db.refresh(workspace)
    return workspace


def restore_workspace(
    db: Session,
    user_id: UUID,
    workspace_id: UUID,
) -> Workspace:
    workspace = get_workspace(
        db=db,
        user_id=user_id,
        workspace_id=workspace_id,
        include_deleted=True,
    )

    workspace.deleted_at = None
    workspace.scheduled_deletion_at = None
    workspace.last_activity_at = datetime.now(UTC)

    db.commit()
    db.refresh(workspace)
    return workspace
