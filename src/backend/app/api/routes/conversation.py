from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.agent.contracts import ConversationTurn
from app.agent.orchestrator import run_analysis_agent
from app.api.deps import get_current_user, get_db
from app.core.exceptions import ConflictError
from app.db.models.conversation import Message
from app.db.models.user import User
from app.schemas.conversation import (
    ChatRequest,
    ChatResponse,
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


@router.post(
    "/datasets/{dataset_id}/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
def chat_with_dataset(
    dataset_id: UUID,
    payload: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ChatResponse:
    # 1. Enforce question limit before running tools
    _conv, used, limit, remaining = get_question_usage(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
    )
    if remaining <= 0:
        raise ConflictError(
            "This conversation has reached the question limit.",
            details={"limit": limit, "used": used},
        )

    # 2. Load conversation history turns
    _conv, existing_messages = list_messages(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
    )
    history = [
        ConversationTurn(role=m.role, content=m.content)  # type: ignore[arg-type]
        for m in existing_messages
        if m.role in ("user", "assistant")
    ]

    # 3. Run the analysis agent (which plans tools, reuses cached results, runs un-cached tools, interprets findings, and persists messages)
    result = run_analysis_agent(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
        question=payload.content,
        active_columns=payload.active_columns or _conv.active_columns_json,
        history=history,
        persist_messages=True,
    )

    user_msg = (
        db.get(Message, result.user_message_id)
        if result.user_message_id
        else None
    )
    asst_msg = (
        db.get(Message, result.assistant_message_id)
        if result.assistant_message_id
        else None
    )

    now = datetime.now(UTC)
    user_response = (
        MessageResponse.model_validate(user_msg)
        if user_msg
        else MessageResponse(
            id=uuid4(),
            conversation_id=_conv.id,
            role="user",
            content=payload.content,
            analysis_run_id=None,
            created_at=now,
        )
    )
    assistant_response = (
        MessageResponse.model_validate(asst_msg)
        if asst_msg
        else MessageResponse(
            id=uuid4(),
            conversation_id=_conv.id,
            role="assistant",
            content=result.assistant_message or "",
            analysis_run_id=result.analysis_run_id,
            created_at=now,
        )
    )

    return ChatResponse(
        user_message=user_response,
        assistant_message=assistant_response,
        analysis_run_id=result.analysis_run_id,
        plan=result.plan.model_dump(mode="json") if result.plan else None,
        interpretation=result.interpretation.model_dump(mode="json")
        if result.interpretation
        else None,
    )
