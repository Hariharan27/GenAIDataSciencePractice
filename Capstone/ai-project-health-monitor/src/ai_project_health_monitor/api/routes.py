from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from ai_project_health_monitor.api.dependencies import (
    ApplicationContainer,
    get_application_container,
)
from ai_project_health_monitor.api.models import (
    HealthTrendResponse,
    ProjectHealthResponse,
    ProjectIndexResponse,
    RiskSignalResponse,
    WeeklyHealthSummaryResponse,
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


@router.get(
    "/projects/{project_id}/health/weekly-summary",
    response_model=WeeklyHealthSummaryResponse,
)
def get_project_weekly_health_summary(
    project_id: str,
    start_date: datetime,
    end_date: datetime,
    container: ApplicationContainer = Depends(
        get_application_container,
    ),
) -> WeeklyHealthSummaryResponse:
    """Generate a weekly project health summary."""

    if not project_id.strip():
        raise HTTPException(
            status_code=400,
            detail="project_id cannot be empty",
        )

    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)

    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    try:
        summary = container.weekly_health_summary_service.generate(
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            key_risks=[],
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return WeeklyHealthSummaryResponse(
        project_id=summary.project_id,
        start_date=start_date,
        end_date=end_date,
        starting_score=summary.starting_score,
        ending_score=summary.ending_score,
        score_change=summary.score_change,
        starting_status=summary.starting_status,
        ending_status=summary.ending_status,
        health_improved=summary.health_improved,
        health_deteriorated=summary.health_deteriorated,
        key_risks=[
            RiskSignalResponse(
                signal_id=risk.signal_id,
                risk_type=risk.risk_type,
                severity=risk.severity,
                confidence=risk.confidence,
                evidence_quote=risk.evidence_quote,
                rationale=risk.rationale,
            )
            for risk in summary.key_risks
        ],
        summary=summary.summary,
        outlook=summary.outlook,
        recommended_actions=summary.recommended_actions,
    )