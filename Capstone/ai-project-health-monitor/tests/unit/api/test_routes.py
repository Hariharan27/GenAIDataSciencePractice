from datetime import UTC, datetime
from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai_project_health_monitor.api.dependencies import (
    ApplicationContainer,
    get_application_container,
)
from ai_project_health_monitor.api.routes import router
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.health_score import HealthScore, HealthStatus
from ai_project_health_monitor.domain.models.health_trend import HealthTrend
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)
from ai_project_health_monitor.domain.models.weekly_health_summary import WeeklyHealthSummary
from ai_project_health_monitor.orchestration.state import ProjectHealthState


def create_test_app(container: ApplicationContainer) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_application_container] = lambda: container
    return app


def test_index_project_returns_indexing_result() -> None:
    container = Mock()

    events = [Mock(), Mock(), Mock()]
    container.ingestion_service.ingest_project.return_value = events
    container.rag_indexer.index.return_value = 3

    client = TestClient(create_test_app(container))

    response = client.post("/api/v1/projects/PROJ-001/index")

    assert response.status_code == 200
    assert response.json() == {
        "project_id": "PROJ-001",
        "events_ingested": 3,
        "chunks_indexed": 3,
    }

    container.ingestion_service.ingest_project.assert_called_once_with(
        "PROJ-001",
    )
    container.rag_indexer.index.assert_called_once_with(events)


def test_index_project_rejects_empty_project_id() -> None:
    container = Mock()

    client = TestClient(create_test_app(container))

    response = client.post("/api/v1/projects/%20/index")

    assert response.status_code == 400
    assert response.json() == {
        "detail": "project_id cannot be empty",
    }


def test_analyze_project_health_returns_health_result() -> None:
    container = Mock()

    container.project_health_monitor.analyze.return_value = ProjectHealthState(
        project_id="PROJ-001",
        query="project health assessment",
        primary_risks=[],
        health_score=HealthScore(
            project_id="PROJ-001",
            score=85.0,
            status=HealthStatus.HEALTHY,
            contributing_risks=[],
            calculated_at=datetime(2026, 9, 9, tzinfo=UTC),
            rationale="Project is progressing well.",
        ),
        summary=None,
        alert_triggered=False,
    )

    client = TestClient(create_test_app(container))

    response = client.post(
        "/api/v1/projects/PROJ-001/health",
        json={"query": "What risks are affecting the project?"},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["project_id"] == "PROJ-001"
    assert body["health_score"] == 85.0
    assert body["health_status"] == "healthy"
    assert body["rationale"] == "Project is progressing well."
    assert body["risks"] == []
    assert body["summary"] is None
    assert body["alert_triggered"] is False

    assert body["summary"] is None
    assert body["alert_triggered"] is False

    container.project_health_monitor.analyze.assert_called_once_with("PROJ-001")

def test_analyze_project_health_returns_risk_details() -> None:
    container = Mock()

    evidence = Evidence(
        event_id="EVT-JIRA-001",
        source_type=SourceType.JIRA,
        source_id="EVT-JIRA-001",
        content=(
            "Payment API integration is blocked because external API "
            "credentials are missing."
        ),
        occurred_at=datetime(2026, 9, 1, tzinfo=UTC),
    )

    risk = RiskSignal(
        signal_id="risk-001",
        project_id="PROJ-001",
        event_id="EVT-JIRA-001",
        risk_type=RiskType.BLOCKER,
        severity=RiskSeverity.HIGH,
        confidence=0.95,
        evidence=evidence,
        evidence_quote=(
            "Payment API integration is blocked because external API "
            "credentials are missing."
        ),
        rationale=(
            "The payment API integration is blocked by missing "
            "credentials."
        ),
    )

    health_score = HealthScore(
        project_id="PROJ-001",
        score=65.0,
        status="at_risk",
        contributing_risks=["risk-001"],
        calculated_at=datetime(2026, 9, 9, tzinfo=UTC),
        rationale="Project has a high-severity blocker.",
    )

    container.project_health_monitor.analyze.return_value = ProjectHealthState(
        project_id="PROJ-001",
        query="project health assessment",
        primary_risks=[risk],
        health_score=health_score,
        summary=None,
        alert_triggered=False,
    )
    client = TestClient(create_test_app(container))

    response = client.post(
        "/api/v1/projects/PROJ-001/health",
        json={"query": "What risks are affecting the project?"},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["project_id"] == "PROJ-001"
    assert body["health_score"] == 65.0
    assert body["health_status"] == "at_risk"
    assert body["alert_triggered"] is False

    assert body["risks"] == [
        {
            "signal_id": "risk-001",
            "risk_type": "blocker",
            "severity": "high",
            "confidence": 0.95,
            "evidence_quote": (
                "Payment API integration is blocked because external API "
                "credentials are missing."
            ),
            "rationale": (
                "The payment API integration is blocked by missing "
                "credentials."
            ),
        }
    ]

def test_analyze_project_health_does_not_require_query() -> None:
    container = Mock()
    container.project_health_monitor.analyze.return_value = ProjectHealthState(
        project_id="PROJ-001",
        query="project health assessment",
        health_score=HealthScore(
            project_id="PROJ-001",
            score=80.0,
            status=HealthStatus.HEALTHY,
            contributing_risks=[],
            calculated_at=datetime(2026, 9, 9, tzinfo=UTC),
            rationale="Project is healthy.",
        ),
    )

    client = TestClient(create_test_app(container))

    response = client.post(
        "/api/v1/projects/PROJ-001/health",
    )

    assert response.status_code == 200
    assert response.json()["project_id"] == "PROJ-001"

    container.project_health_monitor.analyze.assert_called_once_with("PROJ-001")

def test_analyze_project_health_rejects_empty_project_id() -> None:
    container = Mock()

    client = TestClient(create_test_app(container))

    response = client.post(
        "/api/v1/projects/%20/health",
        json={"query": "What risks are affecting the project?"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "project_id cannot be empty",
    }

def test_get_project_health_trend_returns_trend() -> None:
    container = Mock()

    trend = HealthTrend(
        project_id="PROJ-001",
        current_score=65.0,
        previous_score=80.0,
        current_status=HealthStatus.AT_RISK,
        score_change=-15.0,
    )

    container.project_health_monitor.get_trend.return_value = trend
    client = TestClient(create_test_app(container))

    response = client.get("/api/v1/projects/PROJ-001/health/trend")

    assert response.status_code == 200
    assert response.json() == {
        "project_id": "PROJ-001",
        "current_score": 65.0,
        "previous_score": 80.0,
        "current_status": "at_risk",
        "score_change": -15.0,
    }

    container.project_health_monitor.get_trend.assert_called_once_with(
        "PROJ-001",
    )


def test_get_project_health_trend_returns_404_when_history_missing() -> None:
    container = Mock()
    container.project_health_monitor.get_trend.return_value = None
    client = TestClient(create_test_app(container))

    response = client.get("/api/v1/projects/PROJ-999/health/trend")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No health history found for project PROJ-999",
    }


def test_get_project_health_trend_rejects_empty_project_id() -> None:
    container = Mock()
    client = TestClient(create_test_app(container))

    response = client.get("/api/v1/projects/%20/health/trend")

    assert response.status_code == 400
    assert response.json() == {
        "detail": "project_id cannot be empty",
    }

    container.project_health_monitor.get_trend.assert_not_called()

def test_get_project_weekly_health_summary_returns_summary() -> None:
    container = Mock()

    summary = WeeklyHealthSummary(
        project_id="PROJ-001",
        starting_score=82.0,
        ending_score=61.0,
        score_change=-21.0,
        starting_status=HealthStatus.HEALTHY,
        ending_status=HealthStatus.AT_RISK,
        health_improved=False,
        health_deteriorated=True,
        summary="Project health deteriorated during the week.",
        outlook="Release risk remains elevated.",
        recommended_actions=[
            "Resolve the payment integration blocker.",
        ],
    )

    container.weekly_health_summary_service.generate.return_value = summary

    client = TestClient(create_test_app(container))

    response = client.get(
        "/api/v1/projects/PROJ-001/health/weekly-summary"
        "?start_date=2026-09-01T00:00:00"
        "&end_date=2026-09-07T23:59:59"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["project_id"] == "PROJ-001"
    assert body["starting_score"] == 82.0
    assert body["ending_score"] == 61.0
    assert body["score_change"] == -21.0
    assert body["starting_status"] == "healthy"
    assert body["ending_status"] == "at_risk"
    assert body["health_deteriorated"] is True
    assert body["summary"] == "Project health deteriorated during the week."

    container.weekly_health_summary_service.generate.assert_called_once()


def test_get_project_weekly_health_summary_rejects_empty_project_id() -> None:
    container = Mock()

    client = TestClient(create_test_app(container))

    response = client.get(
        "/api/v1/projects/%20/health/weekly-summary"
        "?start_date=2026-09-01T00:00:00"
        "&end_date=2026-09-07T23:59:59"
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "project_id cannot be empty",
    }

    container.weekly_health_summary_service.generate.assert_not_called()

def test_get_project_weekly_health_summary_returns_400_for_invalid_range() -> None:
    container = Mock()

    container.weekly_health_summary_service.generate.side_effect = ValueError(
        "start_date cannot be after end_date"
    )

    client = TestClient(create_test_app(container))

    response = client.get(
        "/api/v1/projects/PROJ-001/health/weekly-summary"
        "?start_date=2026-09-07T00:00:00"
        "&end_date=2026-09-01T00:00:00"
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "start_date cannot be after end_date",
    }