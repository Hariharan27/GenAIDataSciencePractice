from datetime import UTC, datetime

from ai_project_health_monitor.domain.models.project_event import (
    ProjectEvent,
    SourceType,
)
from ai_project_health_monitor.ingestion.connectors.base import (
    ProjectSourceConnector,
)
from ai_project_health_monitor.ingestion.service import IngestionService


class StubConnector(ProjectSourceConnector):
    """Test connector returning predefined project events."""

    def __init__(self, events: list[ProjectEvent]) -> None:
        self._events = events

    def fetch_events(self, project_id: str) -> list[ProjectEvent]:
        return [
            event
            for event in self._events
            if event.project_id == project_id
        ]


def test_ingestion_service_combines_events_from_multiple_sources() -> None:
    events = [
        ProjectEvent(
            event_id="EMAIL-001",
            project_id="PROJ-001",
            source_type=SourceType.EMAIL,
            source_id="EMAIL-001",
            content="Client is concerned about delivery.",
            occurred_at=datetime(2026, 9, 3, 11, tzinfo=UTC),
        ),
        ProjectEvent(
            event_id="JIRA-001",
            project_id="PROJ-001",
            source_type=SourceType.JIRA,
            source_id="JIRA-101",
            content="Backend task is blocked.",
            occurred_at=datetime(2026, 9, 3, 10, tzinfo=UTC),
        ),
    ]

    service = IngestionService(
        connectors=[StubConnector(events)],
    )

    result = service.ingest_project("PROJ-001")

    assert len(result) == 2
    assert result[0].source_type == SourceType.JIRA
    assert result[1].source_type == SourceType.EMAIL


def test_ingestion_service_returns_empty_list_when_no_events() -> None:
    service = IngestionService(
        connectors=[StubConnector([])],
    )

    result = service.ingest_project("PROJ-001")

    assert result == []