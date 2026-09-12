from datetime import UTC, datetime

import pytest

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.orchestration.nodes.return_previous_health import (
    ReturnPreviousHealthNode,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.persistence.health_snapshot import (
    ProjectHealthSnapshot,
)


def _snapshot() -> ProjectHealthSnapshot:
    evidence = Evidence(
        event_id="EVT-001",
        source_type="jira",
        source_id="JIRA-001",
        content="Payment API is blocked.",
        occurred_at=datetime(2026, 9, 1, tzinfo=UTC),
    )

    risk = RiskSignal(
        signal_id="SIG-001",
        project_id="PROJ-001",
        event_id="EVT-001",
        risk_type=RiskType.BLOCKER,
        severity=RiskSeverity.HIGH,
        confidence=0.9,
        evidence=evidence,
        evidence_quote=evidence.content,
        rationale="Payment API is blocked.",
    )

    return ProjectHealthSnapshot(
        project_id="PROJ-001",
        health_score=81.0,
        health_status=HealthStatus.HEALTHY,
        risk_signals=[risk],
        evidence_fingerprint="same-fingerprint",
        calculated_at=datetime(2026, 9, 1, tzinfo=UTC),
    )


def test_returns_previous_health_score_without_recalculation() -> None:
    node = ReturnPreviousHealthNode()

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health",
        evidence_fingerprint="same-fingerprint",
        previous_health_snapshot=_snapshot(),
        evidence_changed=False,
    )

    result = node(state)

    health_score = result["health_score"]

    assert health_score.project_id == "PROJ-001"
    assert health_score.score == 81.0
    assert health_score.status == HealthStatus.HEALTHY
    assert health_score.calculated_at == datetime(
        2026,
        9,
        1,
        tzinfo=UTC,
    )
    assert result["primary_risks"] == state.previous_health_snapshot.risk_signals
    assert result["risk_signals"] == state.previous_health_snapshot.risk_signals


def test_requires_previous_snapshot() -> None:
    node = ReturnPreviousHealthNode()

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health",
        evidence_fingerprint="same-fingerprint",
        evidence_changed=False,
    )

    with pytest.raises(
        ValueError,
        match="previous_health_snapshot must exist",
    ):
        node(state)