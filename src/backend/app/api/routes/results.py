## Fetch saved run output, tool results, and chart artifacts.
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.schemas.result import (
    AnalysisArtifactListResponse,
    AnalysisArtifactResponse,
    AnalysisRunHistoryItem,
    AnalysisRunHistoryResponse,
    AnalysisRunResultsResponse,
)
from app.services.analysis_service import (
    get_analysis_results,
    list_analysis_artifacts,
    list_analysis_runs_for_dataset,
)

router = APIRouter(tags=["Results"])


@router.get(
    "/datasets/{dataset_id}/analysis-runs",
    response_model=AnalysisRunHistoryResponse,
)
def list_dataset_analysis_runs(
    dataset_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AnalysisRunHistoryResponse:
    runs = list_analysis_runs_for_dataset(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
    )
    return AnalysisRunHistoryResponse(
        analysis_runs=[
            AnalysisRunHistoryItem.model_validate(run)
            for run in runs
        ]
    )


@router.get(
    "/analysis-runs/{analysis_run_id}/results",
    response_model=AnalysisRunResultsResponse,
)
def get_run_results(
    analysis_run_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AnalysisRunResultsResponse:
    return AnalysisRunResultsResponse.model_validate(
        get_analysis_results(
            db=db,
            user_id=current_user.id,
            analysis_run_id=analysis_run_id,
        )
    )


@router.get(
    "/analysis-runs/{analysis_run_id}/artifacts",
    response_model=AnalysisArtifactListResponse,
)
def get_run_artifacts(
    analysis_run_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AnalysisArtifactListResponse:
    artifacts = list_analysis_artifacts(
        db=db,
        user_id=current_user.id,
        analysis_run_id=analysis_run_id,
    )
    return AnalysisArtifactListResponse(
        artifacts=[
            AnalysisArtifactResponse.model_validate(artifact)
            for artifact in artifacts
        ]
    )
