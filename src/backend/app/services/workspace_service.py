from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError
from app.db.models.analysis_run import AnalysisRun
from app.db.models.artifact import Artifact
from app.db.models.conversation import Conversation
from app.db.models.dataset import Dataset, DatasetVersion
from app.db.models.workspace import Workspace
from app.services.storage_service import delete_object

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


def get_workspace_reopen_detail(
    db: Session,
    user_id: UUID,
    workspace_id: UUID,
) -> dict[str, object]:
    workspace = get_workspace(
        db=db,
        user_id=user_id,
        workspace_id=workspace_id,
    )

    datasets = list(
        db.scalars(
            select(Dataset)
            .options(selectinload(Dataset.current_version))
            .where(Dataset.workspace_id == workspace.id)
            .order_by(Dataset.created_at.desc())
        )
    )
    recent_runs = list(
        db.scalars(
            select(AnalysisRun)
            .options(selectinload(AnalysisRun.tool_executions))
            .where(AnalysisRun.workspace_id == workspace.id)
            .order_by(AnalysisRun.created_at.desc())
            .limit(10)
        )
    )
    conversations = list(
        db.scalars(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.workspace_id == workspace.id)
            .order_by(Conversation.updated_at.desc(), Conversation.created_at.desc())
        )
    )

    return {
        "workspace": workspace,
        "datasets": datasets,
        "recent_runs": recent_runs,
        "conversations": conversations,
    }


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


def _workspace_storage_keys(db: Session, workspace_id: UUID) -> list[str]:
    dataset_keys = list(
        db.scalars(
            select(DatasetVersion.storage_key)
            .join(DatasetVersion.dataset)
            .where(Dataset.workspace_id == workspace_id)
        )
    )
    artifact_keys = list(
        db.scalars(
            select(Artifact.storage_key)
            .join(Artifact.analysis_run)
            .where(AnalysisRun.workspace_id == workspace_id)
        )
    )
    return [*dataset_keys, *artifact_keys]


def purge_expired_workspaces(db: Session) -> int:
    now = datetime.now(UTC)
    expired = list(
        db.scalars(
            select(Workspace).where(
                Workspace.scheduled_deletion_at.is_not(None),
                Workspace.scheduled_deletion_at <= now,
            )
        )
    )

    purged = 0
    for workspace in expired:
        storage_keys = _workspace_storage_keys(db, workspace.id)
        db.delete(workspace)
        db.commit()
        purged += 1

        for storage_key in storage_keys:
            delete_object(storage_key)

    return purged
