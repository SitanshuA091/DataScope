from __future__ import annotations

import json
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "DataLens API"
    app_version: str = "0.1.0"
    app_env: Literal["local", "development", "staging", "production"] = "development"
    debug: bool = False
    docs_enabled: bool = True
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    # Frontend and CORS
    frontend_url: str = "http://localhost:3000"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    # Secure application session cookie
    session_secret_key: SecretStr
    session_cookie_name: str = "datalens_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 7
    session_same_site: Literal["lax", "strict", "none"] = "lax"

    # Google OAuth sign-in
    google_client_id: str
    google_client_secret: SecretStr
    google_oauth_redirect_uri: str

    # LLM provider keys used through LiteLLM
    google_api_key: SecretStr
    groq_api_key: SecretStr
    planner_model: str = "openai/gpt-oss-120b"
    interpreter_model: str = "gemini-3.5-flash"

    # PostgreSQL
    database_url: str

    # Redis: Celery broker, cache, and worker progress events
    redis_url: str
    cache_ttl_seconds: int = 60 * 60 * 24

    # Cloudflare R2 / S3-compatible object storage
    r2_endpoint_url: str
    r2_access_key_id: SecretStr
    r2_secret_access_key: SecretStr
    r2_bucket_name: str
    r2_region_name: str = "auto"

    # Upload and analysis limits
    max_upload_size_mb: int = 25
    max_dataset_rows: int = 200_000
    max_dataset_columns: int = 100
    max_active_jobs_per_user: int = 2
    max_tools_per_run: int = 3
    max_llm_calls_per_run: int = 2
    max_questions_per_conversation: int = 10
    max_llm_sample_rows: int = 20

    # Celery worker limits
    celery_worker_concurrency: int = 1
    celery_task_soft_time_limit_seconds: int = 240
    celery_task_time_limit_seconds: int = 300
    celery_retry_max_attempts: int = 3

    # Retention policy
    workspace_retention_days: int = 30
    workspace_recovery_days: int = 7

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value

        value = value.strip()

        if value.startswith("["):
            return json.loads(value)

        return [
            origin.strip().rstrip("/")
            for origin in value.split(",")
            if origin.strip()
        ]


settings = Settings()