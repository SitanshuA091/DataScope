from __future__ import annotations

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
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test_analysis_tasks.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("R2_ENDPOINT_URL", "http://localhost")
os.environ.setdefault("R2_ACCESS_KEY_ID", "test-r2-access-key-id")
os.environ.setdefault("R2_SECRET_ACCESS_KEY", "test-r2-secret-access-key")
os.environ.setdefault("R2_BUCKET_NAME", "test-r2-bucket")

from app.workers import analysis_tasks

RUN_ID = UUID("ffffffff-6666-6666-6666-666666666666")


class FakeSession:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_execute_analysis_run_task_opens_session_and_executes(monkeypatch) -> None:
    session = FakeSession()
    captured: dict[str, object] = {}

    monkeypatch.setattr(analysis_tasks, "SessionLocal", lambda: session)

    def fake_execute_analysis_run(db, analysis_run_id):
        captured["db"] = db
        captured["analysis_run_id"] = analysis_run_id

    monkeypatch.setattr(
        analysis_tasks,
        "execute_analysis_run",
        fake_execute_analysis_run,
    )

    result = analysis_tasks.execute_analysis_run_task.run(str(RUN_ID))

    assert result == str(RUN_ID)
    assert captured == {
        "db": session,
        "analysis_run_id": RUN_ID,
    }
    assert session.closed is True
