## Persist and load dataset chat messages and question limits.
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.schemas.conversation import (
    ConversationColumnsUpdate,
    ConversationOpenRequest,
    ConversationResponse,
    MessageCreate,
    MessageListResponse,
    MessageResponse,
    QuestionUsageResponse,
)
from app.services.context_service import (
    create_or_reopen_conversation,
    get_question_usage,
    list_messages,
    save_message,
    update_active_columns,
)

router = APIRouter(tags=["Conversations"])


@router.post(
    "/datasets/{dataset_id}/conversation",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
)
def open_dataset_conversation(
    dataset_id: UUID,
    payload: ConversationOpenRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ConversationResponse:
    conversation = create_or_reopen_conversation(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
        active_columns=payload.active_columns,
    )

    return ConversationResponse.model_validate(conversation)


@router.patch(
    "/conversations/{conversation_id}/columns",
    response_model=ConversationResponse,
)
def update_conversation_columns(
    conversation_id: UUID,
    payload: ConversationColumnsUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ConversationResponse:
    conversation = update_active_columns(
        db=db,
        user_id=current_user.id,
        conversation_id=conversation_id,
        active_columns=payload.active_columns,
    )

    return ConversationResponse.model_validate(conversation)


@router.post(
    "/datasets/{dataset_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_dataset_message(
    dataset_id: UUID,
    payload: MessageCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MessageResponse:
    message = save_message(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
        role=payload.role,
        content=payload.content,
        analysis_run_id=payload.analysis_run_id,
    )

    return MessageResponse.model_validate(message)


@router.get(
    "/datasets/{dataset_id}/messages",
    response_model=MessageListResponse,
)
def list_dataset_messages(
    dataset_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MessageListResponse:
    conversation, messages = list_messages(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
    )

    return MessageListResponse(
        conversation=ConversationResponse.model_validate(conversation),
        messages=[
            MessageResponse.model_validate(message) for message in messages
        ],
    )


@router.get(
    "/datasets/{dataset_id}/question-usage",
    response_model=QuestionUsageResponse,
)
def get_dataset_question_usage(
    dataset_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> QuestionUsageResponse:
    conversation, used, limit, remaining = get_question_usage(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
    )

    return QuestionUsageResponse(
        conversation_id=conversation.id,
        used=used,
        limit=limit,
        remaining=remaining,
    )
