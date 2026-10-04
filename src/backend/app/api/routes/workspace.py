from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceConversationSummary,
    WorkspaceDetailResponse,
    WorkspaceListResponse,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.workspace_service import (
    create_workspace,
    get_workspace_reopen_detail,
    list_workspaces,
    rename_workspace,
    restore_workspace,
    schedule_workspace_deletion,
)

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_workspace(
    payload: WorkspaceCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WorkspaceResponse:
    workspace = create_workspace(
        db=db,
        user_id=current_user.id,
        title=payload.title,
    )

    return WorkspaceResponse.model_validate(workspace)


@router.get("", response_model=WorkspaceListResponse)
def list_user_workspaces(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WorkspaceListResponse:
    workspaces = list_workspaces(
        db=db,
        user_id=current_user.id,
    )

    return WorkspaceListResponse(
        workspaces=[
            WorkspaceResponse.model_validate(workspace)
            for workspace in workspaces
        ]
    )


@router.get("/{workspace_id}", response_model=WorkspaceDetailResponse)
def get_user_workspace(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WorkspaceDetailResponse:
    detail = get_workspace_reopen_detail(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id,
    )

    return WorkspaceDetailResponse(
        workspace=WorkspaceResponse.model_validate(detail["workspace"]),
        datasets=[
            {
                "dataset": dataset,
                "current_version": dataset.current_version,
            }
            for dataset in detail["datasets"]
        ],
        recent_runs=detail["recent_runs"],
        conversations=[
            WorkspaceConversationSummary(
                conversation=conversation,
                messages=list(conversation.messages),
            )
            for conversation in detail["conversations"]
        ],
    )


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def rename_user_workspace(
    workspace_id: UUID,
    payload: WorkspaceUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WorkspaceResponse:
    workspace = rename_workspace(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id,
        title=payload.title,
    )

    return WorkspaceResponse.model_validate(workspace)


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user_workspace(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    schedule_workspace_deletion(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{workspace_id}/restore", response_model=WorkspaceResponse)
def restore_user_workspace(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WorkspaceResponse:
    workspace = restore_workspace(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id,
    )

    return WorkspaceResponse.model_validate(workspace)
