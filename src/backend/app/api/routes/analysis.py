## Create analysis jobs, job status, retry, cancellation.
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.schemas.analysis import (
    AnalysisCreateRequest,
    AnalysisRunResponse,
    AnalysisRunSubmissionResponse,
    AnalysisToolListResponse,
)
from app.services.analysis_service import (
    available_analysis_tools,
    cancel_analysis_run,
    get_analysis_run,
    retry_analysis_run,
    submit_analysis_run,
)

router = APIRouter(tags=["Analysis"])


@router.get(
    "/analysis/tools",
    response_model=AnalysisToolListResponse,
)
def list_analysis_tools() -> AnalysisToolListResponse:
    return AnalysisToolListResponse(tools=available_analysis_tools())


@router.post(
    "/datasets/{dataset_id}/analysis",
    response_model=AnalysisRunSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_dataset_analysis(
    dataset_id: UUID,
    payload: AnalysisCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AnalysisRunSubmissionResponse:
    run, execution_mode = submit_analysis_run(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
        tools=[
            tool.model_dump(mode="json")
            for tool in payload.tools
        ],
        include_plots=payload.include_plots,
    )

    return AnalysisRunSubmissionResponse(
        id=run.id,
        status=run.status,
        execution_mode=execution_mode,
        dataset_version_id=run.dataset_version_id,
        created_at=run.created_at,
    )


@router.post(
    "/datasets/{dataset_id}/analysis-runs",
    response_model=AnalysisRunSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_dataset_analysis_run(
    dataset_id: UUID,
    payload: AnalysisCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AnalysisRunSubmissionResponse:
    return create_dataset_analysis(
        dataset_id=dataset_id,
        payload=payload,
        db=db,
        current_user=current_user,
    )


@router.get(
    "/analysis-runs/{analysis_run_id}",
    response_model=AnalysisRunResponse,
)
def get_dataset_analysis_run(
    analysis_run_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AnalysisRunResponse:
    run = get_analysis_run(
        db=db,
        user_id=current_user.id,
        analysis_run_id=analysis_run_id,
    )

    return AnalysisRunResponse.model_validate(run)


@router.post(
    "/analysis-runs/{analysis_run_id}/retry",
    response_model=AnalysisRunResponse,
)
def retry_dataset_analysis_run(
    analysis_run_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AnalysisRunResponse:
    run = retry_analysis_run(
        db=db,
        user_id=current_user.id,
        analysis_run_id=analysis_run_id,
    )

    return AnalysisRunResponse.model_validate(run)


@router.post(
    "/analysis-runs/{analysis_run_id}/cancel",
    response_model=AnalysisRunResponse,
)
def cancel_dataset_analysis_run(
    analysis_run_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AnalysisRunResponse:
    run = cancel_analysis_run(
        db=db,
        user_id=current_user.id,
        analysis_run_id=analysis_run_id,
    )

    return AnalysisRunResponse.model_validate(run)
