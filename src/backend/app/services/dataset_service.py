from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

import pandas as pd
from pandas.errors import ParserError
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.db.models.dataset import Dataset, DatasetVersion
from app.services.storage_service import delete_object, upload_bytes
from app.services.workspace_service import get_workspace

CSV_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
}
VALIDATION_STATUS_VALID = "valid"


class DatasetValidationError(AppError):
    error_code = "dataset_validation_error"
    default_message = "The uploaded dataset is invalid."


def _validate_upload_metadata(
    *,
    filename: str,
    content_type: str | None,
    file_size: int,
) -> None:
    if not filename.lower().endswith(".csv"):
        raise DatasetValidationError("Only CSV uploads are supported in V1.")

    if content_type and content_type not in CSV_CONTENT_TYPES:
        raise DatasetValidationError("The uploaded file must be a CSV.")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if file_size > max_bytes:
        raise DatasetValidationError(
            f"CSV uploads are limited to {settings.max_upload_size_mb} MB.",
            details={"max_size_mb": settings.max_upload_size_mb},
        )

    if file_size == 0:
        raise DatasetValidationError("The uploaded CSV is empty.")


def _schema_overview(frame: pd.DataFrame) -> list[dict[str, object]]:
    return [
        {
            "name": str(column),
            "dtype": str(frame[column].dtype),
            "nullable": bool(frame[column].isna().any()),
            "missing_count": int(frame[column].isna().sum()),
        }
        for column in frame.columns
    ]


def validate_csv(content: bytes) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    try:
        frame = pd.read_csv(BytesIO(content), nrows=settings.max_dataset_rows + 1)
    except UnicodeDecodeError as exc:
        raise DatasetValidationError(
            "The CSV encoding could not be read. Please upload a UTF-8 CSV."
        ) from exc
    except ParserError as exc:
        raise DatasetValidationError(
            "The CSV could not be parsed. Check for malformed rows or delimiters."
        ) from exc
    except ValueError as exc:
        raise DatasetValidationError("The uploaded CSV could not be read.") from exc

    if frame.empty and len(frame.columns) == 0:
        raise DatasetValidationError("The uploaded CSV has no columns.")

    if len(frame.index) > settings.max_dataset_rows:
        raise DatasetValidationError(
            f"CSV uploads are limited to {settings.max_dataset_rows} rows.",
            details={"max_rows": settings.max_dataset_rows},
        )

    if len(frame.columns) > settings.max_dataset_columns:
        raise DatasetValidationError(
            f"CSV uploads are limited to {settings.max_dataset_columns} columns.",
            details={"max_columns": settings.max_dataset_columns},
        )

    return frame, _schema_overview(frame)


def _dataset_name_from_filename(filename: str) -> str:
    stem = Path(filename).stem.strip()
    return stem[:255] or "Untitled dataset"


def _get_workspace_dataset(db: Session, workspace_id: UUID) -> Dataset | None:
    return db.scalar(
        select(Dataset)
        .where(Dataset.workspace_id == workspace_id)
        .order_by(Dataset.created_at.asc())
        .limit(1)
    )


def _next_version_number(db: Session, dataset_id: UUID) -> int:
    latest = db.scalar(
        select(func.max(DatasetVersion.version_number)).where(
            DatasetVersion.dataset_id == dataset_id
        )
    )
    return int(latest or 0) + 1


def upload_dataset(
    *,
    db: Session,
    user_id: UUID,
    workspace_id: UUID,
    filename: str,
    content: bytes,
    content_type: str | None = None,
) -> tuple[Dataset, DatasetVersion]:
    workspace = get_workspace(
        db=db,
        user_id=user_id,
        workspace_id=workspace_id,
    )

    _validate_upload_metadata(
        filename=filename,
        content_type=content_type,
        file_size=len(content),
    )
    frame, schema_json = validate_csv(content)

    dataset = _get_workspace_dataset(db, workspace_id)
    if dataset is None:
        dataset = Dataset(
            workspace_id=workspace_id,
            name=_dataset_name_from_filename(filename),
        )
        db.add(dataset)
        db.flush()

    version_number = _next_version_number(db, dataset.id)
    storage_key = (
        f"datasets/{workspace_id}/{dataset.id}/"
        f"v{version_number}-{uuid4()}.csv"
    )
    checksum = sha256(content).hexdigest()

    upload_bytes(
        storage_key=storage_key,
        content=content,
        content_type=content_type or "text/csv",
    )

    version = DatasetVersion(
        dataset_id=dataset.id,
        version_number=version_number,
        original_filename=filename,
        storage_key=storage_key,
        checksum=checksum,
        file_size=len(content),
        row_count=len(frame.index),
        column_count=len(frame.columns),
        schema_json=schema_json,
        validation_status=VALIDATION_STATUS_VALID,
        validation_error=None,
    )
    db.add(version)
    db.flush()

    dataset.current_version_id = version.id
    workspace.last_activity_at = datetime.now(UTC)

    db.commit()
    db.refresh(dataset)
    db.refresh(version)
    return dataset, version


def list_workspace_datasets(
    *,
    db: Session,
    user_id: UUID,
    workspace_id: UUID,
) -> list[Dataset]:
    get_workspace(db=db, user_id=user_id, workspace_id=workspace_id)

    return list(
        db.scalars(
            select(Dataset)
            .options(selectinload(Dataset.current_version))
            .where(Dataset.workspace_id == workspace_id)
            .order_by(Dataset.created_at.desc())
        )
    )


def get_dataset_for_user(
    *,
    db: Session,
    user_id: UUID,
    dataset_id: UUID,
) -> Dataset:
    dataset = db.scalar(
        select(Dataset)
        .join(Dataset.workspace)
        .options(selectinload(Dataset.current_version))
        .where(
            Dataset.id == dataset_id,
            Dataset.workspace.has(user_id=user_id),
        )
    )

    if dataset is None:
        raise NotFoundError("Dataset was not found.")

    return dataset


def get_dataset_overview(
    *,
    db: Session,
    user_id: UUID,
    dataset_id: UUID,
) -> tuple[Dataset, DatasetVersion]:
    dataset = get_dataset_for_user(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
    )

    if dataset.current_version is None:
        raise ConflictError("Dataset has no validated versions.")

    return dataset, dataset.current_version


def delete_dataset(
    *,
    db: Session,
    user_id: UUID,
    dataset_id: UUID,
) -> None:
    dataset = get_dataset_for_user(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
    )

    versions = list(
        db.scalars(
            select(DatasetVersion).where(DatasetVersion.dataset_id == dataset.id)
        )
    )
    storage_keys = [version.storage_key for version in versions]

    db.delete(dataset)
    db.commit()

    for storage_key in storage_keys:
        delete_object(storage_key)
