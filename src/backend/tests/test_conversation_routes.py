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
os.environ.setdefault(
    "DATABASE_URL",
    "sqlite+pysqlite:///./test_conversation_routes.db",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("R2_ENDPOINT_URL", "http://localhost")
os.environ.setdefault("R2_ACCESS_KEY_ID", "test-r2-access-key-id")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test-r2-secret-access-key")
os.environ.setdefault("R2_BUCKET_NAME", "test-r2-bucket")

from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import conversation as conversation_routes
from app.core.exceptions import ConflictError, NotFoundError
from app.main import app

USER_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = UUID("22222222-2222-2222-2222-222222222222")
WORKSPACE_ID = UUID("33333333-3333-3333-3333-333333333333")
DATASET_ID = UUID("44444444-4444-4444-4444-444444444444")
VERSION_ID = UUID("55555555-5555-5555-5555-555555555555")
CONVERSATION_ID = UUID("66666666-6666-6666-6666-666666666666")
MESSAGE_ID = UUID("77777777-7777-7777-7777-777777777777")
NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)


def _conversation(active_columns: list[str] | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=CONVERSATION_ID,
        workspace_id=WORKSPACE_ID,
        dataset_version_id=VERSION_ID,
        active_columns_json=active_columns or [],
        created_at=NOW,
        updated_at=NOW,
    )


def _message(
    *,
    message_id: UUID = MESSAGE_ID,
    role: str = "user",
    content: str = "What columns have missing values?",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=message_id,
        conversation_id=CONVERSATION_ID,
        role=role,
        content=content,
        analysis_run_id=None,
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


def test_open_dataset_conversation_scopes_to_current_user(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_create_or_reopen_conversation(
        db,
        user_id,
        dataset_id,
        active_columns,
    ):
        captured["user_id"] = user_id
        captured["dataset_id"] = dataset_id
        captured["active_columns"] = active_columns
        return _conversation(active_columns=active_columns)

    monkeypatch.setattr(
        conversation_routes,
        "create_or_reopen_conversation",
        fake_create_or_reopen_conversation,
    )

    response = TestClient(app).post(
        f"/api/v1/datasets/{DATASET_ID}/conversation",
        json={"active_columns": ["age", "income"]},
    )

    assert response.status_code == 200
    assert captured == {
        "user_id": USER_ID,
        "dataset_id": DATASET_ID,
        "active_columns": ["age", "income"],
    }
    assert response.json()["active_columns_json"] == ["age", "income"]


def test_update_conversation_columns_scopes_to_current_user(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_update_active_columns(
        db,
        user_id,
        conversation_id,
        active_columns,
    ):
        captured["user_id"] = user_id
        captured["conversation_id"] = conversation_id
        captured["active_columns"] = active_columns
        return _conversation(active_columns=active_columns)

    monkeypatch.setattr(
        conversation_routes,
        "update_active_columns",
        fake_update_active_columns,
    )

    response = TestClient(app).patch(
        f"/api/v1/conversations/{CONVERSATION_ID}/columns",
        json={"active_columns": ["region"]},
    )

    assert response.status_code == 200
    assert captured == {
        "user_id": USER_ID,
        "conversation_id": CONVERSATION_ID,
        "active_columns": ["region"],
    }
    assert response.json()["active_columns_json"] == ["region"]


def test_save_dataset_message_enforces_current_user_scope(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_save_message(
        db,
        user_id,
        dataset_id,
        role,
        content,
        analysis_run_id,
    ):
        captured["user_id"] = user_id
        captured["dataset_id"] = dataset_id
        captured["role"] = role
        captured["content"] = content
        captured["analysis_run_id"] = analysis_run_id
        return _message(role=role, content=content)

    monkeypatch.setattr(conversation_routes, "save_message", fake_save_message)

    response = TestClient(app).post(
        f"/api/v1/datasets/{DATASET_ID}/messages",
        json={"role": "user", "content": "Show missing values"},
    )

    assert response.status_code == 201
    assert captured == {
        "user_id": USER_ID,
        "dataset_id": DATASET_ID,
        "role": "user",
        "content": "Show missing values",
        "analysis_run_id": None,
    }
    assert response.json()["content"] == "Show missing values"


def test_save_dataset_message_returns_409_at_question_limit(monkeypatch) -> None:
    def fake_save_message(
        db,
        user_id,
        dataset_id,
        role,
        content,
        analysis_run_id,
    ):
        assert user_id == USER_ID
        raise ConflictError(
            "This conversation has reached the question limit.",
            details={"limit": 10, "used": 10},
        )

    monkeypatch.setattr(conversation_routes, "save_message", fake_save_message)

    response = TestClient(app).post(
        f"/api/v1/datasets/{DATASET_ID}/messages",
        json={"role": "user", "content": "One more question"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["details"] == {"limit": 10, "used": 10}


def test_list_dataset_messages_returns_ordered_messages(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_list_messages(db, user_id, dataset_id):
        captured["user_id"] = user_id
        captured["dataset_id"] = dataset_id
        return (
            _conversation(),
            [
                _message(content="Question"),
                _message(message_id=uuid4(), role="assistant", content="Answer"),
            ],
        )

    monkeypatch.setattr(conversation_routes, "list_messages", fake_list_messages)

    response = TestClient(app).get(f"/api/v1/datasets/{DATASET_ID}/messages")

    assert response.status_code == 200
    assert captured == {
        "user_id": USER_ID,
        "dataset_id": DATASET_ID,
    }
    body = response.json()
    assert body["conversation"]["id"] == str(CONVERSATION_ID)
    assert [message["content"] for message in body["messages"]] == [
        "Question",
        "Answer",
    ]


def test_question_usage_scopes_to_current_user(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_get_question_usage(db, user_id, dataset_id):
        captured["user_id"] = user_id
        captured["dataset_id"] = dataset_id
        return _conversation(), 3, 10, 7

    monkeypatch.setattr(
        conversation_routes,
        "get_question_usage",
        fake_get_question_usage,
    )

    response = TestClient(app).get(
        f"/api/v1/datasets/{DATASET_ID}/question-usage"
    )

    assert response.status_code == 200
    assert captured == {
        "user_id": USER_ID,
        "dataset_id": DATASET_ID,
    }
    assert response.json() == {
        "conversation_id": str(CONVERSATION_ID),
        "used": 3,
        "limit": 10,
        "remaining": 7,
    }


def test_open_conversation_returns_404_when_dataset_not_owned(monkeypatch) -> None:
    def fake_create_or_reopen_conversation(
        db,
        user_id,
        dataset_id,
        active_columns,
    ):
        assert user_id == USER_ID
        assert user_id != OTHER_USER_ID
        raise NotFoundError("Dataset was not found.")

    monkeypatch.setattr(
        conversation_routes,
        "create_or_reopen_conversation",
        fake_create_or_reopen_conversation,
    )

    response = TestClient(app).post(
        f"/api/v1/datasets/{uuid4()}/conversation",
        json={"active_columns": []},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
