from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

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
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test_analysis_routes.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("R2_ENDPOINT_URL", "http://localhost")
os.environ.setdefault("R2_ACCESS_KEY_ID", "test-r2-access-key-id")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test-r2-secret-access-key")
os.environ.setdefault("R2_BUCKET_NAME", "test-r2-bucket")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import deps
from app.api.routes import analysis as analysis_routes
from app.core.exceptions import ConflictError, NotFoundError
from app.db.base import Base
from app.db.models.analysis_run import AnalysisRun
from app.db.models.dataset import Dataset, DatasetVersion
from app.db.models.tool_execution import ToolExecution
from app.db.models.user import User
from app.db.models.workspace import Workspace
from app.main import app
from app.services import analysis_service

USER_ID = UUID("aaaaaaaa-1111-1111-1111-111111111111")
OTHER_USER_ID = UUID("bbbbbbbb-2222-2222-2222-222222222222")
WORKSPACE_ID = UUID("cccccccc-3333-3333-3333-333333333333")
DATASET_ID = UUID("dddddddd-4444-4444-4444-444444444444")
VERSION_ID = UUID("eeeeeeee-5555-5555-5555-555555555555")
RUN_ID = UUID("ffffffff-6666-6666-6666-666666666666")
EXECUTION_ID = UUID("abcdefab-7777-7777-7777-777777777777")
NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)
CSV_BYTES = b"age,income,region\n33,10,north\n44,,south\n"


def _execution() -> SimpleNamespace:
    return SimpleNamespace(
        id=EXECUTION_ID,
        analysis_run_id=RUN_ID,
        tool_name="quality",
        arguments_json={},
        status="completed",
        result_json={"tool": "quality"},
        error_json=None,
        timings_json={"duration_ms": 1.5},
        created_at=NOW,
        started_at=NOW,
        completed_at=NOW,
    )


def _run(*, status: str = "completed") -> SimpleNamespace:
    return SimpleNamespace(
        id=RUN_ID,
        workspace_id=WORKSPACE_ID,
        dataset_version_id=VERSION_ID,
        request_json={"dataset_id": str(DATASET_ID)},
        selected_tools_json=[{"name": "quality", "arguments": {}}],
        status=status,
        results_json={"quality": {"tool": "quality"}},
        error_json=None,
        timings_json={"duration_ms": 2.0},
        created_at=NOW,
        started_at=NOW,
        completed_at=NOW,
        updated_at=NOW,
        tool_executions=[_execution()],
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


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    with SessionLocal() as session:
        user = User(
            id=USER_ID,
            google_sub="google-user",
            email="user@example.com",
            name="Test User",
        )
        workspace = Workspace(
            id=WORKSPACE_ID,
            user_id=USER_ID,
            title="Analysis workspace",
        )
        dataset = Dataset(
            id=DATASET_ID,
            workspace_id=WORKSPACE_ID,
            name="customers",
        )
        version = DatasetVersion(
            id=VERSION_ID,
            dataset_id=DATASET_ID,
            version_number=1,
            original_filename="customers.csv",
            storage_key="datasets/customers.csv",
            checksum="a" * 64,
            file_size=len(CSV_BYTES),
            row_count=2,
            column_count=3,
            schema_json=[
                {"name": "age", "dtype": "int64", "nullable": False},
                {"name": "income", "dtype": "float64", "nullable": True},
                {"name": "region", "dtype": "object", "nullable": False},
            ],
            validation_status="valid",
            validation_error=None,
        )
        session.add_all([user, workspace, dataset, version])
        session.flush()
        dataset.current_version_id = VERSION_ID
        session.commit()

        yield session

    engine.dispose()


def test_create_dataset_analysis_scopes_to_current_user(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_submit_analysis_run(
        db,
        user_id,
        dataset_id,
        tools,
        include_plots,
    ):
        captured["user_id"] = user_id
        captured["dataset_id"] = dataset_id
        captured["tools"] = tools
        captured["include_plots"] = include_plots
        return _run(status="pending"), "queued"

    monkeypatch.setattr(
        analysis_routes,
        "submit_analysis_run",
        fake_submit_analysis_run,
    )

    response = TestClient(app).post(
        f"/api/v1/datasets/{DATASET_ID}/analysis",
        json={
            "include_plots": False,
            "tools": [{"name": "quality", "arguments": {}}],
        },
    )

    assert response.status_code == 201
    assert captured == {
        "user_id": USER_ID,
        "dataset_id": DATASET_ID,
        "tools": [{"name": "quality", "arguments": {}}],
        "include_plots": False,
    }
    body = response.json()
    assert body["id"] == str(RUN_ID)
    assert body["status"] == "pending"
    assert body["execution_mode"] == "queued"
    assert body["dataset_version_id"] == str(VERSION_ID)


def test_list_analysis_tools_returns_registry_metadata() -> None:
    response = TestClient(app).get("/api/v1/analysis/tools")

    assert response.status_code == 200
    tool_names = {tool["name"] for tool in response.json()["tools"]}
    assert {"high_level", "column", "relationships", "quality"} <= tool_names


def test_get_analysis_run_scopes_to_current_user(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_get_analysis_run(db, user_id, analysis_run_id):
        captured["user_id"] = user_id
        captured["analysis_run_id"] = analysis_run_id
        return _run()

    monkeypatch.setattr(
        analysis_routes,
        "get_analysis_run",
        fake_get_analysis_run,
    )

    response = TestClient(app).get(f"/api/v1/analysis-runs/{RUN_ID}")

    assert response.status_code == 200
    assert captured == {
        "user_id": USER_ID,
        "analysis_run_id": RUN_ID,
    }
    assert response.json()["status"] == "completed"


def test_retry_analysis_run_scopes_to_current_user(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_retry_analysis_run(db, user_id, analysis_run_id):
        captured["user_id"] = user_id
        captured["analysis_run_id"] = analysis_run_id
        return _run()

    monkeypatch.setattr(
        analysis_routes,
        "retry_analysis_run",
        fake_retry_analysis_run,
    )

    response = TestClient(app).post(f"/api/v1/analysis-runs/{RUN_ID}/retry")

    assert response.status_code == 200
    assert captured == {
        "user_id": USER_ID,
        "analysis_run_id": RUN_ID,
    }


def test_cancel_analysis_run_scopes_to_current_user(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_cancel_analysis_run(db, user_id, analysis_run_id):
        captured["user_id"] = user_id
        captured["analysis_run_id"] = analysis_run_id
        return _run(status="cancelled")

    monkeypatch.setattr(
        analysis_routes,
        "cancel_analysis_run",
        fake_cancel_analysis_run,
    )

    response = TestClient(app).post(f"/api/v1/analysis-runs/{RUN_ID}/cancel")

    assert response.status_code == 200
    assert captured == {
        "user_id": USER_ID,
        "analysis_run_id": RUN_ID,
    }
    assert response.json()["status"] == "cancelled"


def test_get_analysis_run_returns_404_when_not_owned(monkeypatch) -> None:
    def fake_get_analysis_run(db, user_id, analysis_run_id):
        assert user_id == USER_ID
        assert user_id != OTHER_USER_ID
        raise NotFoundError("Analysis run was not found.")

    monkeypatch.setattr(
        analysis_routes,
        "get_analysis_run",
        fake_get_analysis_run,
    )

    response = TestClient(app).get(f"/api/v1/analysis-runs/{RUN_ID}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_create_analysis_run_persists_and_executes_tools(
    db_session,
    monkeypatch,
) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_run_tool(name, frame, **kwargs):
        calls.append((name, kwargs))
        return {
            "tool": name,
            "rows": len(frame.index),
            "columns": list(frame.columns),
            "arguments": kwargs,
        }

    monkeypatch.setattr(analysis_service, "download_bytes", lambda key: CSV_BYTES)
    monkeypatch.setattr(analysis_service, "run_tool", fake_run_tool)

    run = analysis_service.create_analysis_run(
        db=db_session,
        user_id=USER_ID,
        dataset_id=DATASET_ID,
        tools=[
            {"name": "quality", "arguments": {"high_cardinality_threshold": 0.5}},
            {"name": "column", "arguments": {"columns": ["age"]}},
        ],
        include_plots=True,
    )

    assert run.status == "completed"
    assert run.request_json["include_plots"] is True
    assert run.selected_tools_json == [
        {"name": "quality", "arguments": {"high_cardinality_threshold": 0.5}},
        {"name": "column", "arguments": {"columns": ["age"]}},
    ]
    assert run.results_json["quality"]["rows"] == 2
    assert run.results_json["column"]["arguments"] == {"columns": ["age"]}
    assert run.error_json is None
    assert [execution.status for execution in run.tool_executions] == [
        "completed",
        "completed",
    ]
    assert calls == [
        ("quality", {"high_cardinality_threshold": 0.5}),
        ("column", {"columns": ["age"]}),
    ]

    persisted_executions = list(
        db_session.scalars(
            select(ToolExecution).where(ToolExecution.analysis_run_id == run.id)
        )
    )
    assert [execution.tool_name for execution in persisted_executions] == [
        "quality",
        "column",
    ]


def test_submit_analysis_run_executes_small_single_tool_inline(
    db_session,
    monkeypatch,
) -> None:
    monkeypatch.setattr(analysis_service, "download_bytes", lambda key: CSV_BYTES)
    monkeypatch.setattr(
        analysis_service,
        "run_tool",
        lambda name, frame, **kwargs: {"tool": name, "rows": len(frame.index)},
    )

    run, execution_mode = analysis_service.submit_analysis_run(
        db=db_session,
        user_id=USER_ID,
        dataset_id=DATASET_ID,
        tools=[{"name": "quality", "arguments": {}}],
    )

    assert execution_mode == "inline"
    assert run.status == "completed"
    assert run.results_json == {"quality": {"tool": "quality", "rows": 2}}


def test_submit_analysis_run_queues_multi_tool_request(
    db_session,
    monkeypatch,
) -> None:
    dispatched: list[UUID] = []

    def fake_dispatch(analysis_run_id):
        dispatched.append(analysis_run_id)
        return "task-123"

    monkeypatch.setattr(analysis_service, "_dispatch_analysis_run", fake_dispatch)

    run, execution_mode = analysis_service.submit_analysis_run(
        db=db_session,
        user_id=USER_ID,
        dataset_id=DATASET_ID,
        tools=[
            {"name": "quality", "arguments": {}},
            {"name": "column", "arguments": {"columns": ["age"]}},
        ],
    )

    assert execution_mode == "queued"
    assert run.status == "pending"
    assert dispatched == [run.id]
    assert run.timings_json["execution_mode"] == "queued"
    assert run.timings_json["celery_task_id"] == "task-123"


def test_submit_analysis_run_queues_plot_request(
    db_session,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        analysis_service,
        "_dispatch_analysis_run",
        lambda analysis_run_id: "task-plot",
    )

    run, execution_mode = analysis_service.submit_analysis_run(
        db=db_session,
        user_id=USER_ID,
        dataset_id=DATASET_ID,
        tools=[{"name": "quality", "arguments": {}}],
        include_plots=True,
    )

    assert execution_mode == "queued"
    assert run.status == "pending"
    assert run.timings_json["celery_task_id"] == "task-plot"


def test_submit_analysis_run_queues_relationship_request(
    db_session,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        analysis_service,
        "_dispatch_analysis_run",
        lambda analysis_run_id: "task-relationships",
    )

    run, execution_mode = analysis_service.submit_analysis_run(
        db=db_session,
        user_id=USER_ID,
        dataset_id=DATASET_ID,
        tools=[{"name": "relationships", "arguments": {"columns": ["age", "income"]}}],
    )

    assert execution_mode == "queued"
    assert run.status == "pending"
    assert run.timings_json["celery_task_id"] == "task-relationships"


def test_submit_analysis_run_queues_large_dataset(
    db_session,
    monkeypatch,
) -> None:
    version = db_session.get(DatasetVersion, VERSION_ID)
    version.row_count = analysis_service.settings.inline_analysis_max_rows + 1
    db_session.commit()
    monkeypatch.setattr(
        analysis_service,
        "_dispatch_analysis_run",
        lambda analysis_run_id: "task-large",
    )

    run, execution_mode = analysis_service.submit_analysis_run(
        db=db_session,
        user_id=USER_ID,
        dataset_id=DATASET_ID,
        tools=[{"name": "quality", "arguments": {}}],
    )

    assert execution_mode == "queued"
    assert run.status == "pending"
    assert run.timings_json["celery_task_id"] == "task-large"


def test_submit_analysis_run_marks_failed_when_queue_dispatch_fails(
    db_session,
    monkeypatch,
) -> None:
    def fail_dispatch(analysis_run_id):
        raise RuntimeError("redis unavailable")

    monkeypatch.setattr(analysis_service, "_dispatch_analysis_run", fail_dispatch)

    run, execution_mode = analysis_service.submit_analysis_run(
        db=db_session,
        user_id=USER_ID,
        dataset_id=DATASET_ID,
        tools=[
            {"name": "quality", "arguments": {}},
            {"name": "column", "arguments": {"columns": ["age"]}},
        ],
    )

    assert execution_mode == "queued"
    assert run.status == "failed"
    assert run.error_json == {
        "type": "RuntimeError",
        "message": "Analysis run could not be queued.",
        "dispatch_error": "redis unavailable",
    }


def test_execute_analysis_run_marks_run_failed_when_dataset_read_fails(
    db_session,
    monkeypatch,
) -> None:
    run = AnalysisRun(
        workspace_id=WORKSPACE_ID,
        dataset_version_id=VERSION_ID,
        request_json={"dataset_id": str(DATASET_ID)},
        selected_tools_json=[{"name": "quality", "arguments": {}}],
        status="pending",
    )
    db_session.add(run)
    db_session.flush()
    db_session.add(
        ToolExecution(
            analysis_run_id=run.id,
            tool_name="quality",
            arguments_json={},
            status="pending",
        )
    )
    db_session.commit()

    def fail_download(storage_key):
        raise RuntimeError(f"missing object: {storage_key}")

    monkeypatch.setattr(analysis_service, "download_bytes", fail_download)

    executed = analysis_service.execute_analysis_run(
        db=db_session,
        analysis_run_id=run.id,
    )

    assert executed.status == "failed"
    assert executed.results_json is None
    assert executed.error_json == {
        "type": "RuntimeError",
        "message": "missing object: datasets/customers.csv",
    }
    assert executed.tool_executions[0].status == "pending"


def test_execute_analysis_run_records_failed_tool_and_continues(
    db_session,
    monkeypatch,
) -> None:
    run = AnalysisRun(
        workspace_id=WORKSPACE_ID,
        dataset_version_id=VERSION_ID,
        request_json={"dataset_id": str(DATASET_ID)},
        selected_tools_json=[
            {"name": "quality", "arguments": {}},
            {"name": "column", "arguments": {"columns": ["age"]}},
        ],
        status="pending",
    )
    db_session.add(run)
    db_session.flush()
    db_session.add_all(
        [
            ToolExecution(
                analysis_run_id=run.id,
                tool_name="quality",
                arguments_json={},
                status="pending",
            ),
            ToolExecution(
                analysis_run_id=run.id,
                tool_name="column",
                arguments_json={"columns": ["age"]},
                status="pending",
            ),
        ]
    )
    db_session.commit()

    def fake_run_tool(name, frame, **kwargs):
        if name == "quality":
            raise ValueError("quality failed")
        return {"tool": name, "columns": kwargs["columns"]}

    monkeypatch.setattr(analysis_service, "download_bytes", lambda key: CSV_BYTES)
    monkeypatch.setattr(analysis_service, "run_tool", fake_run_tool)

    executed = analysis_service.execute_analysis_run(
        db=db_session,
        analysis_run_id=run.id,
    )

    executions_by_name = {
        execution.tool_name: execution for execution in executed.tool_executions
    }
    assert executed.status == "failed"
    assert executed.results_json == {"column": {"tool": "column", "columns": ["age"]}}
    assert executed.error_json["tools"] == [
        {
            "tool": "quality",
            "error": {"type": "ValueError", "message": "quality failed"},
        }
    ]
    assert executions_by_name["quality"].status == "failed"
    assert executions_by_name["quality"].error_json["message"] == "quality failed"
    assert executions_by_name["column"].status == "completed"
    assert executions_by_name["column"].result_json == {
        "tool": "column",
        "columns": ["age"],
    }


def test_retry_analysis_run_resets_failed_execution_and_runs_again(
    db_session,
    monkeypatch,
) -> None:
    run = AnalysisRun(
        workspace_id=WORKSPACE_ID,
        dataset_version_id=VERSION_ID,
        request_json={"dataset_id": str(DATASET_ID)},
        selected_tools_json=[{"name": "quality", "arguments": {}}],
        status="failed",
        results_json={"stale": True},
        error_json={"old": "error"},
        timings_json={"duration_ms": 10},
        started_at=NOW,
        completed_at=NOW,
    )
    db_session.add(run)
    db_session.flush()
    db_session.add(
        ToolExecution(
            analysis_run_id=run.id,
            tool_name="quality",
            arguments_json={},
            status="failed",
            result_json={"stale": True},
            error_json={"old": "error"},
            timings_json={"duration_ms": 10},
            started_at=NOW,
            completed_at=NOW,
        )
    )
    db_session.commit()

    monkeypatch.setattr(analysis_service, "download_bytes", lambda key: CSV_BYTES)
    monkeypatch.setattr(
        analysis_service,
        "run_tool",
        lambda name, frame, **kwargs: {"tool": name, "rows": len(frame.index)},
    )

    retried = analysis_service.retry_analysis_run(
        db=db_session,
        user_id=USER_ID,
        analysis_run_id=run.id,
    )

    assert retried.status == "completed"
    assert retried.results_json == {"quality": {"tool": "quality", "rows": 2}}
    assert retried.error_json is None
    assert retried.tool_executions[0].status == "completed"
    assert retried.tool_executions[0].error_json is None
    assert retried.tool_executions[0].result_json == {"tool": "quality", "rows": 2}


def test_retry_analysis_run_rejects_non_terminal_run(db_session) -> None:
    run = AnalysisRun(
        workspace_id=WORKSPACE_ID,
        dataset_version_id=VERSION_ID,
        request_json={"dataset_id": str(DATASET_ID)},
        selected_tools_json=[],
        status="running",
    )
    db_session.add(run)
    db_session.commit()

    with pytest.raises(ConflictError, match="Only finished analysis runs"):
        analysis_service.retry_analysis_run(
            db=db_session,
            user_id=USER_ID,
            analysis_run_id=run.id,
        )


def test_cancel_analysis_run_marks_pending_and_running_executions_cancelled(
    db_session,
) -> None:
    run = AnalysisRun(
        workspace_id=WORKSPACE_ID,
        dataset_version_id=VERSION_ID,
        request_json={"dataset_id": str(DATASET_ID)},
        selected_tools_json=[],
        status="running",
    )
    db_session.add(run)
    db_session.flush()
    db_session.add_all(
        [
            ToolExecution(
                analysis_run_id=run.id,
                tool_name="quality",
                arguments_json={},
                status="pending",
            ),
            ToolExecution(
                analysis_run_id=run.id,
                tool_name="column",
                arguments_json={},
                status="running",
            ),
            ToolExecution(
                analysis_run_id=run.id,
                tool_name="high_level",
                arguments_json={},
                status="completed",
            ),
        ]
    )
    db_session.commit()

    cancelled = analysis_service.cancel_analysis_run(
        db=db_session,
        user_id=USER_ID,
        analysis_run_id=run.id,
    )

    statuses = {
        execution.tool_name: execution.status
        for execution in cancelled.tool_executions
    }
    assert cancelled.status == "cancelled"
    assert cancelled.completed_at is not None
    assert statuses == {
        "quality": "cancelled",
        "column": "cancelled",
        "high_level": "completed",
    }


def test_create_analysis_run_rejects_unknown_tool(db_session) -> None:
    with pytest.raises(analysis_service.AnalysisValidationError) as exc_info:
        analysis_service.create_analysis_run(
            db=db_session,
            user_id=USER_ID,
            dataset_id=DATASET_ID,
            tools=[{"name": "does_not_exist", "arguments": {}}],
        )

    assert exc_info.value.details == {"unknown_tool": "does_not_exist"}
    assert db_session.scalar(select(AnalysisRun)) is None
