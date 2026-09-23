## CSV upload, validation, lightweight schema overview, versions.
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.schemas.dataset import (
    DatasetListItem,
    DatasetListResponse,
    DatasetOverviewResponse,
    DatasetResponse,
    DatasetUploadResponse,
    DatasetVersionResponse,
)
from app.services.dataset_service import (
    delete_dataset,
    get_dataset_overview,
    list_workspace_datasets,
    upload_dataset,
)

router = APIRouter(tags=["Datasets"])


@router.post(
    "/workspaces/{workspace_id}/datasets",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_workspace_dataset(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: Annotated[UploadFile, File()],
) -> DatasetUploadResponse:
    content = await file.read()
    dataset, version = upload_dataset(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id,
        filename=file.filename or "dataset.csv",
        content=content,
        content_type=file.content_type,
    )

    return DatasetUploadResponse(
        dataset=DatasetResponse.model_validate(dataset),
        version=DatasetVersionResponse.model_validate(version),
    )


@router.get(
    "/workspaces/{workspace_id}/datasets",
    response_model=DatasetListResponse,
)
def list_workspace_dataset_versions(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DatasetListResponse:
    datasets = list_workspace_datasets(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id,
    )

    return DatasetListResponse(
        datasets=[
            DatasetListItem(
                dataset=DatasetResponse.model_validate(dataset),
                current_version=(
                    DatasetVersionResponse.model_validate(
                        dataset.current_version
                    )
                    if dataset.current_version is not None
                    else None
                ),
            )
            for dataset in datasets
        ]
    )


@router.get(
    "/datasets/{dataset_id}/overview",
    response_model=DatasetOverviewResponse,
)
def get_dataset_schema_overview(
    dataset_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DatasetOverviewResponse:
    dataset, version = get_dataset_overview(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
    )

    return DatasetOverviewResponse(
        dataset_id=dataset.id,
        workspace_id=dataset.workspace_id,
        dataset_name=dataset.name,
        current_version_id=version.id,
        version_number=version.version_number,
        original_filename=version.original_filename,
        row_count=version.row_count,
        column_count=version.column_count,
        columns=[column["name"] for column in version.schema_json],
        schema_json=version.schema_json,
        validation_status=version.validation_status,
        validation_error=version.validation_error,
        created_at=version.created_at,
    )


@router.delete(
    "/datasets/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user_dataset(
    dataset_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    delete_dataset(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
