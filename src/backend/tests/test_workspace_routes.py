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
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test_workspace_routes.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("R2_ENDPOINT_URL", "http://localhost")
os.environ.setdefault("R2_ACCESS_KEY_ID", "test-r2-access-key-id")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test-r2-secret-access-key")
os.environ.setdefault("R2_BUCKET_NAME", "test-r2-bucket")

from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import workspace as workspace_routes
from app.core.exceptions import NotFoundError
from app.main import app

USER_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = UUID("22222222-2222-2222-2222-222222222222")
WORKSPACE_ID = UUID("33333333-3333-3333-3333-333333333333")
NOW = datetime(2026, 9, 22, 12, 0, tzinfo=UTC)


def _workspace(
    *,
    workspace_id: UUID = WORKSPACE_ID,
    user_id: UUID = USER_ID,
    title: str = "Analysis workspace",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=workspace_id,
        user_id=user_id,
        title=title,
        last_activity_at=NOW,
        deleted_at=None,
        scheduled_deletion_at=None,
        created_at=NOW,
        updated_at=NOW,
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


def test_create_workspace_scopes_to_current_user(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_create_workspace(db, user_id, title):
        captured["db"] = db
        captured["user_id"] = user_id
        captured["title"] = title
        return _workspace(title=title)

    monkeypatch.setattr(
        workspace_routes,
        "create_workspace",
        fake_create_workspace,
    )

    response = TestClient(app).post(
        "/api/v1/workspaces",
        json={"title": "EDA Sprint"},
    )

    assert response.status_code == 201
    assert captured["user_id"] == USER_ID
    assert captured["title"] == "EDA Sprint"
    assert response.json()["user_id"] == str(USER_ID)


def test_list_workspaces_scopes_to_current_user(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_list_workspaces(db, user_id):
        captured["user_id"] = user_id
        return [_workspace()]

    monkeypatch.setattr(
        workspace_routes,
        "list_workspaces",
        fake_list_workspaces,
    )

    response = TestClient(app).get("/api/v1/workspaces")

    assert response.status_code == 200
    assert captured["user_id"] == USER_ID
    assert response.json()["workspaces"][0]["id"] == str(WORKSPACE_ID)


def test_open_workspace_scopes_to_current_user(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_get_workspace(db, user_id, workspace_id):
        captured["user_id"] = user_id
        captured["workspace_id"] = workspace_id
        return _workspace(workspace_id=workspace_id)

    monkeypatch.setattr(workspace_routes, "get_workspace", fake_get_workspace)

    response = TestClient(app).get(f"/api/v1/workspaces/{WORKSPACE_ID}")

    assert response.status_code == 200
    assert captured == {
        "user_id": USER_ID,
        "workspace_id": WORKSPACE_ID,
    }


def test_open_workspace_returns_404_when_not_owned(monkeypatch) -> None:
    def fake_get_workspace(db, user_id, workspace_id):
        assert user_id == USER_ID
        assert user_id != OTHER_USER_ID
        raise NotFoundError("Workspace was not found.")

    monkeypatch.setattr(workspace_routes, "get_workspace", fake_get_workspace)

    response = TestClient(app).get(f"/api/v1/workspaces/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_rename_workspace_scopes_to_current_user(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_rename_workspace(db, user_id, workspace_id, title):
        captured["user_id"] = user_id
        captured["workspace_id"] = workspace_id
        captured["title"] = title
        return _workspace(workspace_id=workspace_id, title=title)

    monkeypatch.setattr(
        workspace_routes,
        "rename_workspace",
        fake_rename_workspace,
    )

    response = TestClient(app).patch(
        f"/api/v1/workspaces/{WORKSPACE_ID}",
        json={"title": "Renamed workspace"},
    )

    assert response.status_code == 200
    assert captured == {
        "user_id": USER_ID,
        "workspace_id": WORKSPACE_ID,
        "title": "Renamed workspace",
    }
    assert response.json()["title"] == "Renamed workspace"


def test_delete_workspace_scopes_to_current_user(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_schedule_workspace_deletion(db, user_id, workspace_id):
        captured["user_id"] = user_id
        captured["workspace_id"] = workspace_id
        return _workspace(workspace_id=workspace_id)

    monkeypatch.setattr(
        workspace_routes,
        "schedule_workspace_deletion",
        fake_schedule_workspace_deletion,
    )

    response = TestClient(app).delete(f"/api/v1/workspaces/{WORKSPACE_ID}")

    assert response.status_code == 204
    assert response.content == b""
    assert captured == {
        "user_id": USER_ID,
        "workspace_id": WORKSPACE_ID,
    }
