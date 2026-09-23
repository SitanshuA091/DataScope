from __future__ import annotations

from pathlib import Path
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings
from app.core.exceptions import AppError

LOCAL_STORAGE_ROOT = Path(".data/uploads")
R2_CLIENT_CONFIG = Config(
    signature_version="s3v4",
    retries={
        "max_attempts": 3,
        "mode": "standard",
    },
)


class StorageError(AppError):
    error_code = "storage_error"
    default_message = "The file could not be stored."


def _use_local_storage() -> bool:
    return settings.r2_endpoint_url.startswith(("file://", "local://"))


def _local_path(storage_key: str) -> Path:
    return LOCAL_STORAGE_ROOT / storage_key


def _r2_client() -> Any:
    """Create a Cloudflare R2 client through its S3-compatible API."""
    return boto3.client(
        "s3",
        endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key_id.get_secret_value(),
        aws_secret_access_key=settings.r2_secret_access_key.get_secret_value(),
        region_name=settings.r2_region_name,
        config=R2_CLIENT_CONFIG,
    )


def upload_bytes(
    *,
    storage_key: str,
    content: bytes,
    content_type: str = "text/csv",
) -> str:
    if _use_local_storage():
        path = _local_path(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return storage_key

    try:
        _r2_client().put_object(
            Bucket=settings.r2_bucket_name,
            Key=storage_key,
            Body=content,
            ContentType=content_type,
        )
    except (BotoCoreError, ClientError) as exc:
        raise StorageError("The uploaded file could not be stored.") from exc

    return storage_key


def download_bytes(storage_key: str) -> bytes:
    if _use_local_storage():
        try:
            return _local_path(storage_key).read_bytes()
        except OSError as exc:
            raise StorageError("The stored file could not be read.") from exc

    try:
        response = _r2_client().get_object(
            Bucket=settings.r2_bucket_name,
            Key=storage_key,
        )
        return response["Body"].read()
    except (BotoCoreError, ClientError) as exc:
        raise StorageError("The stored file could not be read.") from exc


def delete_object(storage_key: str) -> None:
    if _use_local_storage():
        _local_path(storage_key).unlink(missing_ok=True)
        return

    try:
        _r2_client().delete_object(
            Bucket=settings.r2_bucket_name,
            Key=storage_key,
        )
    except (BotoCoreError, ClientError) as exc:
        raise StorageError("The stored file could not be deleted.") from exc
