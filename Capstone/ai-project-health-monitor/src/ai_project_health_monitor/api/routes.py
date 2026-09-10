from fastapi import APIRouter, Depends, HTTPException

from ai_project_health_monitor.api.dependencies import (
    ApplicationContainer,
    get_application_container,
)
from ai_project_health_monitor.api.models import (
    ProjectHealthResponse,
    ProjectIndexResponse,
    RiskSignalResponse,
    HealthTrendResponse,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["projects"],
)


@router.post(
    "/projects/{project_id}/index",
    response_model=ProjectIndexResponse,
)
def index_project(
    project_id: str,
    container: ApplicationContainer = Depends(
        get_application_container,
    ),
) -> ProjectIndexResponse:
    """Ingest and index all configured sources for a project."""

    if not project_id.strip():
        raise HTTPException(
            status_code=400,
            detail="project_id cannot be empty",
        )

    events = container.ingestion_service.ingest_project(project_id)

    chunks_indexed = container.rag_indexer.index(events)

    return ProjectIndexResponse(
        project_id=project_id,
        events_ingested=len(events),
        chunks_indexed=chunks_indexed,
    )

@router.post(
    "/projects/{project_id}/health",
    response_model=ProjectHealthResponse,
)
def analyze_project_health(
    project_id: str,
    container: ApplicationContainer = Depends(
        get_application_container,
    ),
) -> ProjectHealthResponse:
    """Analyze the current health of a project."""

    if not project_id.strip():
        raise HTTPException(
            status_code=400,
            detail="project_id cannot be empty",
        )

    result = container.project_health_monitor.analyze(project_id)

    health_score = result.health_score

    if health_score is None:
        raise RuntimeError(
            "health_score was not produced by the health workflow"
        )

    risks = [
        RiskSignalResponse(
            signal_id=signal.signal_id,
            risk_type=signal.risk_type,
            severity=signal.severity,
            confidence=signal.confidence,
            evidence_quote=signal.evidence_quote,
            rationale=signal.rationale,
        )
        for signal in result.primary_risks
    ]

    return ProjectHealthResponse(
        project_id=result.project_id,
        health_score=health_score.score,
        health_status=health_score.status,
        rationale=health_score.rationale,
        risks=risks,
        summary=result.summary,
        alert_triggered=result.alert_triggered,
    )

@router.get(
    "/projects/{project_id}/health/trend",
    response_model=HealthTrendResponse,
)
def get_project_health_trend(
    project_id: str,
    container: ApplicationContainer = Depends(
        get_application_container,
    ),
) -> HealthTrendResponse:
    """Return the historical health trend for a project."""
    if not project_id.strip():
        raise HTTPException(
            status_code=400,
            detail="project_id cannot be empty",
        )

    trend = container.project_health_monitor.get_trend(project_id)

    if trend is None:
        raise HTTPException(
            status_code=404,
            detail=f"No health history found for project {project_id}",
        )

    return HealthTrendResponse(
        project_id=trend.project_id,
        current_score=trend.current_score,
        previous_score=trend.previous_score,
        current_status=trend.current_status,
        score_change=trend.score_change,
    )