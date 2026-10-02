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
    AnalysisToolListResponse,
)
from app.services.analysis_service import (
    available_analysis_tools,
    cancel_analysis_run,
    create_analysis_run,
    get_analysis_run,
    retry_analysis_run,
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
    response_model=AnalysisRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_dataset_analysis(
    dataset_id: UUID,
    payload: AnalysisCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AnalysisRunResponse:
    run = create_analysis_run(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
        tools=[
            tool.model_dump(mode="json")
            for tool in payload.tools
        ],
        include_plots=payload.include_plots,
    )

    return AnalysisRunResponse.model_validate(run)


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
