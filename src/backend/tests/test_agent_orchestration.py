from __future__ import annotations

import json
import os
import sys
from pathlib import Path
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
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test_agent.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("R2_ENDPOINT_URL", "http://localhost")
os.environ.setdefault("R2_ACCESS_KEY_ID", "test-r2-access-key-id")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test-r2-secret-access-key")
os.environ.setdefault("R2_BUCKET_NAME", "test-r2-bucket")

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agent.contracts import DatasetColumn, DatasetContext
from app.agent.interpreter import AgentInterpreter
from app.agent.orchestrator import AnalysisAgentOrchestrator
from app.agent.planner import AgentPlanner, AgentPlanningError
from app.db.base import Base
from app.db.models.analysis_run import AnalysisRun
from app.db.models.conversation import Message
from app.db.models.dataset import Dataset, DatasetVersion
from app.db.models.user import User
from app.db.models.workspace import Workspace
from app.services import analysis_service

USER_ID = UUID("aaaaaaaa-1111-1111-1111-111111111111")
WORKSPACE_ID = UUID("cccccccc-3333-3333-3333-333333333333")
DATASET_ID = UUID("dddddddd-4444-4444-4444-444444444444")
VERSION_ID = UUID("eeeeeeee-5555-5555-5555-555555555555")
CSV_BYTES = b"age,income,region\n33,10,north\n44,,south\n"


class FakeLLMClient:
    planner_model = "fake-planner"
    interpreter_model = "fake-interpreter"

    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def complete_json(self, *, model, messages, temperature=0.0):
        self.calls.append(
            {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
        )
        return self.responses.pop(0)

    def complete_text(self, *, model, messages, temperature=0.2):
        raise AssertionError("complete_text should not be used in these tests")


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
                {
                    "name": "region",
                    "dtype": "object",
                    "nullable": False,
                    "missing_count": 0,
                },
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


def _dataset_context() -> DatasetContext:
    return DatasetContext(
        dataset_id=DATASET_ID,
        dataset_version_id=VERSION_ID,
        row_count=2,
        column_count=3,
        columns=[
            DatasetColumn(name="age", dtype="int64"),
            DatasetColumn(name="income", dtype="float64"),
            DatasetColumn(name="region", dtype="object"),
        ],
        active_columns=["age"],
    )


def test_planner_validates_selected_columns() -> None:
    client = FakeLLMClient(
        [
            {
                "intent": "Analyze a missing column",
                "tools": [
                    {
                        "name": "column",
                        "arguments": {"columns": ["missing"]},
                        "reason": "The user asked about a column.",
                    }
                ],
            }
        ]
    )
    planner = AgentPlanner(llm_client=client)

    with pytest.raises(AgentPlanningError) as exc_info:
        planner.plan(
            question="Describe missing",
            dataset_context=_dataset_context(),
        )

    assert exc_info.value.details == {
        "tool": "column",
        "missing_columns": ["missing"],
    }


def test_orchestrator_plans_executes_interprets_and_persists(
    db_session,
    monkeypatch,
) -> None:
    planner_client = FakeLLMClient(
        [
            {
                "intent": "Inspect data quality",
                "tools": [
                    {
                        "name": "quality",
                        "arguments": {"high_cardinality_threshold": 0.5},
                        "reason": "The user asked for quality issues.",
                    }
                ],
            }
        ]
    )
    interpreter_client = FakeLLMClient(
        [
            {
                "answer": "The dataset has one missing income value.",
                "key_findings": ["income has missing values"],
                "limitations": ["Only computed quality output was reviewed."],
                "follow_up_questions": ["Should we inspect income distribution?"],
            }
        ]
    )

    monkeypatch.setattr(analysis_service, "download_bytes", lambda key: CSV_BYTES)
    monkeypatch.setattr(
        analysis_service,
        "run_tool",
        lambda name, frame, **kwargs: {
            "tool": name,
            "missingness": [{"column": "income", "missing_count": 1}],
            "arguments": kwargs,
        },
    )

    orchestrator = AnalysisAgentOrchestrator(
        planner=AgentPlanner(llm_client=planner_client),
        interpreter=AgentInterpreter(llm_client=interpreter_client),
    )

    result = orchestrator.run(
        db=db_session,
        user_id=USER_ID,
        dataset_id=DATASET_ID,
        question="Find data quality issues",
        active_columns=["income"],
    )

    assert result.analysis_run_id is not None
    assert result.interpretation is not None
    assert result.interpretation.answer == "The dataset has one missing income value."
    assert result.plan.tools[0].name == "quality"
    assert "income has missing values" in result.assistant_message

    run = db_session.get(AnalysisRun, result.analysis_run_id)
    assert run is not None
    assert run.status == "completed"
    assert run.results_json["_agent"]["question"] == "Find data quality issues"
    assert run.results_json["_agent"]["interpretation"]["key_findings"] == [
        "income has missing values"
    ]
    assert run.results_json["_agent"]["interpretation"]["answer"] == (
        "The dataset has one missing income value."
    )

    interpreter_payload = json.loads(
        interpreter_client.calls[0]["messages"][1]["content"]
    )
    assert sorted(interpreter_payload) == [
        "dataset_context",
        "question",
        "tool_errors",
        "tool_results",
        "tools",
    ]
    assert interpreter_payload["dataset_context"] == {
        "dataset_id": str(DATASET_ID),
        "dataset_version_id": str(VERSION_ID),
        "row_count": 2,
        "column_count": 3,
        "active_columns": ["income"],
    }
    assert interpreter_payload["tools"] == [
        {
            "name": "quality",
            "arguments": {"high_cardinality_threshold": 0.5},
        }
    ]
    assert "columns" not in interpreter_payload["dataset_context"]
    assert "plan" not in interpreter_payload

    messages = list(
        db_session.scalars(select(Message).order_by(Message.created_at.asc()))
    )
    assert [message.role for message in messages] == ["user", "assistant"]
    assert messages[1].analysis_run_id == result.analysis_run_id


def test_orchestrator_persists_clarification_without_running_tools(
    db_session,
) -> None:
    planner_client = FakeLLMClient(
        [
            {
                "intent": "Needs a target column",
                "requires_clarification": True,
                "clarification_question": "Which column should I analyze?",
                "tools": [],
            }
        ]
    )
    orchestrator = AnalysisAgentOrchestrator(
        planner=AgentPlanner(llm_client=planner_client),
        interpreter=AgentInterpreter(
            llm_client=FakeLLMClient(
                [
                    {
                        "answer": "unused",
                        "key_findings": [],
                        "limitations": [],
                        "follow_up_questions": [],
                    }
                ]
            )
        ),
    )

    result = orchestrator.run(
        db=db_session,
        user_id=USER_ID,
        dataset_id=DATASET_ID,
        question="Compare that",
    )

    assert result.analysis_run_id is None
    assert result.assistant_message == "Which column should I analyze?"
    assert db_session.scalar(select(AnalysisRun)) is None

    messages = list(
        db_session.scalars(select(Message).order_by(Message.created_at.asc()))
    )
    assert [message.content for message in messages] == [
        "Compare that",
        "Which column should I analyze?",
    ]
