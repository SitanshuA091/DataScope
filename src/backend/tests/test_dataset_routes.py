from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

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
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test_dataset_routes.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("R2_ENDPOINT_URL", "http://localhost")
os.environ.setdefault("R2_ACCESS_KEY_ID", "test-r2-access-key-id")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test-r2-secret-access-key")
os.environ.setdefault("R2_BUCKET_NAME", "test-r2-bucket")

from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import datasets as dataset_routes
from app.core.exceptions import NotFoundError
from app.main import app

USER_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = UUID("22222222-2222-2222-2222-222222222222")
WORKSPACE_ID = UUID("33333333-3333-3333-3333-333333333333")
DATASET_ID = UUID("44444444-4444-4444-4444-444444444444")
VERSION_ID = UUID("55555555-5555-5555-5555-555555555555")
NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)


def _schema() -> list[dict[str, object]]:
    return [
        {
            "name": "age",
            "dtype": "int64",
            "nullable": False,
            "missing_count": 0,
        },
        {
            "name": "income",
            "dtype": "float64",
            "nullable": True,
            "missing_count": 1,
        },
    ]


def _dataset() -> SimpleNamespace:
    return SimpleNamespace(
        id=DATASET_ID,
        workspace_id=WORKSPACE_ID,
        name="customers",
        current_version_id=VERSION_ID,
        created_at=NOW,
        updated_at=NOW,
    )


def _version(*, version_number: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        id=VERSION_ID,
        dataset_id=DATASET_ID,
        version_number=version_number,
        original_filename="customers.csv",
        storage_key="datasets/key.csv",
        checksum="a" * 64,
        file_size=24,
        row_count=2,
        column_count=2,
        schema_json=_schema(),
        validation_status="valid",
        validation_error=None,
        created_at=NOW,
    )


def _override_dependencies() -> None:
    app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(
        id=USER_ID,
    )
    app.dependency_overrides[deps.get_db] = lambda: SimpleNamespace()


def setup_function() -> None:
    app.dependency_overrides.clear()
    _override_dependencies()


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_upload_dataset_scopes_to_workspace_owner(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_upload_dataset(
        db,
        user_id,
        workspace_id,
        filename,
        content,
        content_type,
    ):
        captured["user_id"] = user_id
        captured["workspace_id"] = workspace_id
        captured["filename"] = filename
        captured["content"] = content
        captured["content_type"] = content_type
        return _dataset(), _version()

    monkeypatch.setattr(dataset_routes, "upload_dataset", fake_upload_dataset)

    response = TestClient(app).post(
        f"/api/v1/workspaces/{WORKSPACE_ID}/datasets",
        files={"file": ("customers.csv", b"age,income\n33,10\n44,\n", "text/csv")},
    )

    assert response.status_code == 201
    assert captured == {
        "user_id": USER_ID,
        "workspace_id": WORKSPACE_ID,
        "filename": "customers.csv",
        "content": b"age,income\n33,10\n44,\n",
        "content_type": "text/csv",
    }
    body = response.json()
    assert body["dataset"]["id"] == str(DATASET_ID)
    assert body["version"]["schema_json"][0]["name"] == "age"


def test_list_workspace_datasets_scopes_to_current_user(monkeypatch) -> None:
    captured: dict[str, object] = {}
    dataset = _dataset()
    dataset.current_version = _version()

    def fake_list_workspace_datasets(db, user_id, workspace_id):
        captured["user_id"] = user_id
        captured["workspace_id"] = workspace_id
        return [dataset]

    monkeypatch.setattr(
        dataset_routes,
        "list_workspace_datasets",
        fake_list_workspace_datasets,
    )

    response = TestClient(app).get(f"/api/v1/workspaces/{WORKSPACE_ID}/datasets")

    assert response.status_code == 200
    assert captured == {
        "user_id": USER_ID,
        "workspace_id": WORKSPACE_ID,
    }
    assert response.json()["datasets"][0]["current_version"]["id"] == str(VERSION_ID)


def test_get_dataset_overview_scopes_to_current_user(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_get_dataset_overview(db, user_id, dataset_id):
        captured["user_id"] = user_id
        captured["dataset_id"] = dataset_id
        return _dataset(), _version(version_number=2)

    monkeypatch.setattr(
        dataset_routes,
        "get_dataset_overview",
        fake_get_dataset_overview,
    )

    response = TestClient(app).get(f"/api/v1/datasets/{DATASET_ID}/overview")

    assert response.status_code == 200
    assert captured == {
        "user_id": USER_ID,
        "dataset_id": DATASET_ID,
    }
    body = response.json()
    assert body["columns"] == ["age", "income"]
    assert body["version_number"] == 2


def test_get_dataset_overview_returns_404_when_not_owned(monkeypatch) -> None:
    def fake_get_dataset_overview(db, user_id, dataset_id):
        assert user_id == USER_ID
        assert user_id != OTHER_USER_ID
        raise NotFoundError("Dataset was not found.")

    monkeypatch.setattr(
        dataset_routes,
        "get_dataset_overview",
        fake_get_dataset_overview,
    )

    response = TestClient(app).get(f"/api/v1/datasets/{uuid4()}/overview")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_delete_dataset_scopes_to_current_user(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_delete_dataset(db, user_id, dataset_id):
        captured["user_id"] = user_id
        captured["dataset_id"] = dataset_id

    monkeypatch.setattr(dataset_routes, "delete_dataset", fake_delete_dataset)

    response = TestClient(app).delete(f"/api/v1/datasets/{DATASET_ID}")

    assert response.status_code == 204
    assert response.content == b""
    assert captured == {
        "user_id": USER_ID,
        "dataset_id": DATASET_ID,
    }
