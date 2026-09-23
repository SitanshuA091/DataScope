from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.db.models.conversation import Conversation, Message
from app.db.models.dataset import DatasetVersion
from app.services.dataset_service import get_dataset_overview

USER_MESSAGE_ROLE = "user"
ALLOWED_MESSAGE_ROLES = {USER_MESSAGE_ROLE, "assistant", "system"}


class ConversationValidationError(AppError):
    error_code = "conversation_validation_error"
    default_message = "The conversation request is invalid."


def _column_names(dataset_version: DatasetVersion) -> set[str]:
    return {str(column["name"]) for column in dataset_version.schema_json}


def _validate_active_columns(
    dataset_version: DatasetVersion,
    active_columns: list[str],
) -> list[str]:
    normalized = [column.strip() for column in active_columns if column.strip()]
    duplicates = sorted(
        {
            column
            for index, column in enumerate(normalized)
            if column in normalized[:index]
        }
    )
    if duplicates:
        raise ConversationValidationError(
            "Selected columns must be unique.",
            details={"duplicate_columns": duplicates},
        )

    available_columns = _column_names(dataset_version)
    missing_columns = [
        column for column in normalized if column not in available_columns
    ]
    if missing_columns:
        raise ConversationValidationError(
            "One or more selected columns are not in the active dataset version.",
            details={"missing_columns": missing_columns},
        )

    return normalized


def create_or_reopen_conversation(
    *,
    db: Session,
    user_id: UUID,
    dataset_id: UUID,
    active_columns: list[str] | None = None,
) -> Conversation:
    dataset, dataset_version = get_dataset_overview(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
    )

    conversation = db.scalar(
        select(Conversation).where(
            Conversation.workspace_id == dataset.workspace_id,
            Conversation.dataset_version_id == dataset_version.id,
        )
    )

    if conversation is None:
        conversation = Conversation(
            workspace_id=dataset.workspace_id,
            dataset_version_id=dataset_version.id,
            active_columns_json=[],
        )
        db.add(conversation)

    if active_columns is not None:
        conversation.active_columns_json = _validate_active_columns(
            dataset_version,
            active_columns,
        )

    dataset.workspace.last_activity_at = datetime.now(UTC)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation_for_dataset(
    *,
    db: Session,
    user_id: UUID,
    dataset_id: UUID,
) -> Conversation:
    return create_or_reopen_conversation(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
        active_columns=None,
    )


def get_conversation_for_user(
    *,
    db: Session,
    user_id: UUID,
    conversation_id: UUID,
) -> Conversation:
    conversation = db.scalar(
        select(Conversation)
        .join(Conversation.workspace)
        .where(
            Conversation.id == conversation_id,
            Conversation.workspace.has(user_id=user_id),
        )
    )

    if conversation is None:
        raise NotFoundError("Conversation was not found.")

    return conversation


def update_active_columns(
    *,
    db: Session,
    user_id: UUID,
    conversation_id: UUID,
    active_columns: list[str],
) -> Conversation:
    conversation = get_conversation_for_user(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    dataset_version = db.get(DatasetVersion, conversation.dataset_version_id)
    if dataset_version is None:
        raise NotFoundError("Dataset version was not found.")

    conversation.active_columns_json = _validate_active_columns(
        dataset_version,
        active_columns,
    )
    conversation.workspace.last_activity_at = datetime.now(UTC)

    db.commit()
    db.refresh(conversation)
    return conversation


def list_messages(
    *,
    db: Session,
    user_id: UUID,
    dataset_id: UUID,
) -> tuple[Conversation, list[Message]]:
    conversation = get_conversation_for_dataset(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
    )

    messages = list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        )
    )
    return conversation, messages


def get_question_usage(
    *,
    db: Session,
    user_id: UUID,
    dataset_id: UUID,
) -> tuple[Conversation, int, int, int]:
    conversation = get_conversation_for_dataset(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
    )
    used = db.scalar(
        select(func.count(Message.id)).where(
            Message.conversation_id == conversation.id,
            Message.role == USER_MESSAGE_ROLE,
        )
    )
    limit = settings.max_questions_per_conversation
    remaining = max(limit - int(used or 0), 0)
    return conversation, int(used or 0), limit, remaining


def save_message(
    *,
    db: Session,
    user_id: UUID,
    dataset_id: UUID,
    role: str,
    content: str,
    analysis_run_id: UUID | None = None,
) -> Message:
    if role not in ALLOWED_MESSAGE_ROLES:
        raise ConversationValidationError("Message role is not supported.")

    conversation, used, limit, _remaining = get_question_usage(
        db=db,
        user_id=user_id,
        dataset_id=dataset_id,
    )

    if role == USER_MESSAGE_ROLE and used >= limit:
        raise ConflictError(
            "This conversation has reached the question limit.",
            details={"limit": limit, "used": used},
        )

    message = Message(
        conversation_id=conversation.id,
        role=role,
        content=content.strip(),
        analysis_run_id=analysis_run_id,
    )
    db.add(message)
    conversation.workspace.last_activity_at = datetime.now(UTC)

    db.commit()
    db.refresh(message)
    return message
