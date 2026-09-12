from datetime import UTC, datetime
from unittest.mock import Mock

from ai_project_health_monitor.domain.models.health_score import (
    HealthScore,
    HealthStatus,
)
from ai_project_health_monitor.domain.models.risk_signal import RiskSignal
from ai_project_health_monitor.orchestration.nodes.persist_health_snapshot import (
    PersistHealthSnapshotNode,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.persistence.repositories.health_snapshot import (
    HealthSnapshotRepository,
)


def test_persist_health_snapshot_node_saves_health_snapshot() -> None:
    repository = Mock(spec=HealthSnapshotRepository)

    calculated_at = datetime(2026, 9, 10, 10, tzinfo=UTC)
    risk_signal = Mock(spec=RiskSignal)

    health_score = HealthScore(
        project_id="PROJ-001",
        score=60.0,
        status=HealthStatus.AT_RISK,
        contributing_risks=["SIG-001"],
        calculated_at=calculated_at,
        rationale="Project has significant delivery risks.",
    )

    node = PersistHealthSnapshotNode(
        health_snapshot_repository=repository,
    )

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health assessment",
        evidence_fingerprint="test-fingerprint",
        primary_risks=[risk_signal],
        health_score=health_score,
    )

    result = node(state)

    assert result == {}

    repository.save.assert_called_once()
    snapshot = repository.save.call_args.args[0]

    assert snapshot.project_id == "PROJ-001"
    assert snapshot.health_score == 60.0
    assert snapshot.health_status == HealthStatus.AT_RISK
    assert snapshot.risk_signals == [risk_signal]
    assert snapshot.evidence_fingerprint == "test-fingerprint"
    assert snapshot.calculated_at == calculated_at