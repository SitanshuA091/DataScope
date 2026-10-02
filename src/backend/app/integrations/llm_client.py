from __future__ import annotations

import json
import os
from typing import Any, Protocol

from litellm import completion

from app.core.config import settings


class LLMClient(Protocol):
    def complete_json(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        ...

    def complete_text(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
    ) -> str:
        ...


def _configure_provider_env() -> None:
    if "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = settings.google_api_key.get_secret_value()
    if "GROQ_API_KEY" not in os.environ:
        os.environ["GROQ_API_KEY"] = settings.groq_api_key.get_secret_value()


def _message_content(response: Any) -> str:
    try:
        return str(response.choices[0].message.content)
    except AttributeError:
        return str(response["choices"][0]["message"]["content"])


def _strip_json_fence(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


class LiteLLMClient:
    def __init__(
        self,
        *,
        planner_model: str | None = None,
        interpreter_model: str | None = None,
    ) -> None:
        self.planner_model = planner_model or settings.planner_model
        self.interpreter_model = interpreter_model or settings.interpreter_model

    def complete_text(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
    ) -> str:
        _configure_provider_env()
        response = completion(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return _message_content(response).strip()

    def complete_json(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        content = self.complete_text(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        parsed = json.loads(_strip_json_fence(content))
        if not isinstance(parsed, dict):
            raise TypeError("LLM response must be a JSON object.")
        return parsed
