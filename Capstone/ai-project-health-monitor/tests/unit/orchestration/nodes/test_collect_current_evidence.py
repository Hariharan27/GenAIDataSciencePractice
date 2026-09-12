from datetime import UTC, datetime
from unittest.mock import Mock

from ai_project_health_monitor.domain.models.project_event import (
    ProjectEvent,
    SourceType,
)
from ai_project_health_monitor.ingestion.service import IngestionService
from ai_project_health_monitor.orchestration.nodes.collect_current_evidence import (
    CollectCurrentEvidenceNode,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState


def test_collect_current_evidence_calculates_fingerprint() -> None:
    ingestion_service = Mock(spec=IngestionService)
    events = [
        ProjectEvent(
            event_id="EVT-001",
            project_id="PROJ-001",
            source_type=SourceType.JIRA,
            source_id="JIRA-101",
            content="Payment API integration is blocked.",
            occurred_at=datetime(2026, 9, 1, tzinfo=UTC),
        ),
    ]
    ingestion_service.ingest_project.return_value = events

    node = CollectCurrentEvidenceNode(ingestion_service)
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health",
    )

    result = node(state)

    assert isinstance(result["evidence_fingerprint"], str)
    assert len(result["evidence_fingerprint"]) == 64
    ingestion_service.ingest_project.assert_called_once_with("PROJ-001")


def test_collect_current_evidence_produces_stable_fingerprint() -> None:
    ingestion_service = Mock(spec=IngestionService)
    events = [
        ProjectEvent(
            event_id="EVT-001",
            project_id="PROJ-001",
            source_type=SourceType.JIRA,
            source_id="JIRA-101",
            content="Payment API integration is blocked.",
            occurred_at=datetime(2026, 9, 1, tzinfo=UTC),
        ),
    ]
    ingestion_service.ingest_project.return_value = events

    node = CollectCurrentEvidenceNode(ingestion_service)
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health",
    )

    first = node(state)
    second = node(state)

    assert first["evidence_fingerprint"] == second["evidence_fingerprint"]