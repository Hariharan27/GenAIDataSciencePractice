from datetime import UTC, datetime
from unittest.mock import Mock

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.orchestration.nodes.load_previous_health import (
    LoadPreviousHealthNode,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.persistence.health_snapshot import (
    ProjectHealthSnapshot,
)
from ai_project_health_monitor.persistence.repositories.health_snapshot import (
    HealthSnapshotRepository,
)


def test_load_previous_health_returns_latest_snapshot() -> None:
    repository = Mock(spec=HealthSnapshotRepository)
    snapshot = ProjectHealthSnapshot(
        project_id="PROJ-001",
        health_score=81.0,
        health_status=HealthStatus.HEALTHY,
        risk_signals=[],
        calculated_at=datetime(2026, 9, 1, tzinfo=UTC),
        evidence_fingerprint="test-fingerprint",
    )
    repository.get_latest.return_value = snapshot

    node = LoadPreviousHealthNode(repository)
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health",
    )

    result = node(state)

    assert result["previous_health_snapshot"] == snapshot
    repository.get_latest.assert_called_once_with("PROJ-001")


def test_load_previous_health_returns_none_when_no_snapshot_exists() -> None:
    repository = Mock(spec=HealthSnapshotRepository)
    repository.get_latest.return_value = None

    node = LoadPreviousHealthNode(repository)
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health",
    )

    result = node(state)

    assert result["previous_health_snapshot"] is None
    repository.get_latest.assert_called_once_with("PROJ-001")