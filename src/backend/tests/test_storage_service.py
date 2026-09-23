from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("SESSION_SECRET_KEY", "test-session-secret")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-google-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-google-client-secret")
os.environ.setdefault(
    "GOOGLE_OAUTH_REDIRECT_URI",
    "http://localhost/api/v1/auth/google/callback",
)
os.environ.setdefault("GOOGLE_API_KEY", "test-google-api-key")
os.environ.setdefault("GROQ_API_KEY", "test-groq-api-key")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test_storage.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault(
    "R2_ENDPOINT_URL",
    "https://account-id.r2.cloudflarestorage.com",
)
os.environ.setdefault("R2_ACCESS_KEY_ID", "test-r2-access-key-id")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test-r2-secret-access-key")
os.environ.setdefault("R2_BUCKET_NAME", "test-r2-bucket")

from app.services import storage_service


class _Secret:
    def __init__(self, value: str) -> None:
        self.value = value

    def get_secret_value(self) -> str:
        return self.value


def test_r2_client_uses_cloudflare_r2_settings(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        storage_service,
        "settings",
        SimpleNamespace(
            r2_endpoint_url="https://abc123.r2.cloudflarestorage.com",
            r2_access_key_id=_Secret("r2-access-key"),
            r2_secret_access_key=_Secret("r2-secret-key"),
            r2_region_name="auto",
        ),
    )

    def fake_client(service_name, **kwargs):
        captured["service_name"] = service_name
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(storage_service.boto3, "client", fake_client)

    storage_service._r2_client()

    assert captured["service_name"] == "s3"
    assert captured["endpoint_url"] == "https://abc123.r2.cloudflarestorage.com"
    assert captured["aws_access_key_id"] == "r2-access-key"
    assert captured["aws_secret_access_key"] == "r2-secret-key"
    assert captured["region_name"] == "auto"
    assert captured["config"] == storage_service.R2_CLIENT_CONFIG


def test_upload_bytes_writes_to_r2_bucket(monkeypatch) -> None:
    calls: dict[str, object] = {}

    monkeypatch.setattr(storage_service, "_use_local_storage", lambda: False)
    monkeypatch.setattr(
        storage_service,
        "settings",
        SimpleNamespace(r2_bucket_name="datasets-bucket"),
    )

    class FakeR2Client:
        def put_object(self, **kwargs):
            calls.update(kwargs)

    monkeypatch.setattr(storage_service, "_r2_client", lambda: FakeR2Client())

    storage_key = storage_service.upload_bytes(
        storage_key="datasets/workspace/file.csv",
        content=b"a,b\n1,2\n",
        content_type="text/csv",
    )

    assert storage_key == "datasets/workspace/file.csv"
    assert calls == {
        "Bucket": "datasets-bucket",
        "Key": "datasets/workspace/file.csv",
        "Body": b"a,b\n1,2\n",
        "ContentType": "text/csv",
    }
