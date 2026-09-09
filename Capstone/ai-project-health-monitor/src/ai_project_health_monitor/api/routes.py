from fastapi import APIRouter, Depends, HTTPException

from ai_project_health_monitor.api.dependencies import (
    ApplicationContainer,
    get_application_container,
)
from ai_project_health_monitor.api.models import (
    ProjectHealthRequest,
    ProjectHealthResponse,
    ProjectIndexResponse,
    RiskSignalResponse,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState

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
    request: ProjectHealthRequest,
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

    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="query cannot be empty",
        )

    state = ProjectHealthState(
        project_id=project_id,
        query=request.query,
    )

    result = ProjectHealthState.model_validate(
        container.graph.invoke(state)
    )

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