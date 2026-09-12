from datetime import UTC, datetime
from unittest.mock import Mock

from ai_project_health_monitor.analysis.risk_change_detector import (
    RiskChangeDetector,
)
from ai_project_health_monitor.analysis.risk_change_investigator import (
    RiskChangeInvestigator,
)
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)
from ai_project_health_monitor.orchestration.nodes.investigate_risk_changes import (
    InvestigateRiskChangesNode,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.persistence.health_snapshot import (
    ProjectHealthSnapshot,
)
from ai_project_health_monitor.domain.models.risk_change import (
    RiskChange,
    RiskChangeType,
)


def _risk(
    *,
    event_id: str,
    risk_type: RiskType = RiskType.DELAY,
    severity: RiskSeverity = RiskSeverity.HIGH,
) -> RiskSignal:
    evidence = Evidence(
        source_id=f"source-{event_id}",
        source_type="jira",
        project_id="PROJ-001",
        event_id=event_id,
        occurred_at=datetime(2026, 9, 1, tzinfo=UTC),
        content="Project delivery is at risk.",
    )
    return RiskSignal(
        signal_id=f"signal-{event_id}",
        project_id="PROJ-001",
        event_id=event_id,
        risk_type=risk_type,
        severity=severity,
        confidence=0.9,
        evidence=evidence,
        evidence_quote="Project delivery is at risk.",
        rationale="The project update indicates a delivery risk.",
    )


def _snapshot(risks: list[RiskSignal]) -> ProjectHealthSnapshot:
    return ProjectHealthSnapshot(
        project_id="PROJ-001",
        health_score=60.0,
        health_status="at_risk",
        risk_signals=risks,
        calculated_at=datetime(2026, 9, 1, tzinfo=UTC),
        evidence_fingerprint="previous-fingerprint",
    )


def _investigator() -> Mock:
    investigator = Mock(spec=RiskChangeInvestigator)
    investigator.investigate.return_value = []
    return investigator


def test_detects_new_risk() -> None:
    investigator = _investigator()
    node = InvestigateRiskChangesNode(
        risk_change_detector=RiskChangeDetector(),
        risk_change_investigator=investigator,
    )
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health",
        previous_health_snapshot=_snapshot([]),
        risk_signals=[_risk(event_id="EVT-001")],
    )

    result = node(state)

    assert len(result["risk_changes"]) == 1
    change = result["risk_changes"][0]
    assert change.change_type == RiskChangeType.NEW
    assert change.current_risk is not None
    assert change.current_risk.event_id == "EVT-001"


def test_detects_resolved_risk() -> None:
    previous_risk = _risk(event_id="EVT-001")
    investigator = _investigator()
    node = InvestigateRiskChangesNode(
        risk_change_detector=RiskChangeDetector(),
        risk_change_investigator=investigator,
    )
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health",
        previous_health_snapshot=_snapshot([previous_risk]),
        risk_signals=[],
    )

    result = node(state)

    assert len(result["risk_changes"]) == 1
    change = result["risk_changes"][0]
    assert change.change_type == RiskChangeType.RESOLVED
    assert change.previous_risk is not None
    assert change.previous_risk.event_id == "EVT-001"


def test_detects_continuing_risk() -> None:
    previous_risk = _risk(
        event_id="EVT-001",
        severity=RiskSeverity.HIGH,
    )
    current_risk = _risk(
        event_id="EVT-001",
        severity=RiskSeverity.HIGH,
    )
    investigator = _investigator()
    node = InvestigateRiskChangesNode(
        risk_change_detector=RiskChangeDetector(),
        risk_change_investigator=investigator,
    )
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health",
        previous_health_snapshot=_snapshot([previous_risk]),
        risk_signals=[current_risk],
    )

    result = node(state)

    assert len(result["risk_changes"]) == 1
    assert result["risk_changes"][0].change_type == RiskChangeType.CONTINUING


def test_detects_severity_increase() -> None:
    previous_risk = _risk(
        event_id="EVT-001",
        severity=RiskSeverity.MEDIUM,
    )
    current_risk = _risk(
        event_id="EVT-001",
        severity=RiskSeverity.CRITICAL,
    )
    investigator = _investigator()
    node = InvestigateRiskChangesNode(
        risk_change_detector=RiskChangeDetector(),
        risk_change_investigator=investigator,
    )
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health",
        previous_health_snapshot=_snapshot([previous_risk]),
        risk_signals=[current_risk],
    )

    result = node(state)

    assert len(result["risk_changes"]) == 1
    assert (
        result["risk_changes"][0].change_type
        == RiskChangeType.SEVERITY_INCREASED
    )

def test_uses_investigator_changes_when_available() -> None:
    previous_risk = _risk(event_id="EVT-001")
    current_risk = _risk(event_id="EVT-002")

    investigator_change = RiskChange(
        project_id="PROJ-001",
        change_type=RiskChangeType.CONTINUING,
        previous_risk=previous_risk,
        current_risk=current_risk,
        rationale="The new project event represents the same underlying delivery risk.",
    )

    investigator = _investigator()
    investigator.investigate.return_value = [investigator_change]

    node = InvestigateRiskChangesNode(
        risk_change_detector=RiskChangeDetector(),
        risk_change_investigator=investigator,
    )

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health",
        previous_health_snapshot=_snapshot([previous_risk]),
        risk_signals=[current_risk],
        evidence=[current_risk.evidence],
    )

    result = node(state)

    assert result["risk_changes"] == [investigator_change]
    investigator.investigate.assert_called_once()

def test_uses_deterministic_changes_when_investigator_returns_no_changes() -> None:
    previous_risk = _risk(event_id="EVT-001")

    investigator = _investigator()

    node = InvestigateRiskChangesNode(
        risk_change_detector=RiskChangeDetector(),
        risk_change_investigator=investigator,
    )

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health",
        previous_health_snapshot=_snapshot([previous_risk]),
        risk_signals=[],
        evidence=[],
    )

    result = node(state)

    assert len(result["risk_changes"]) == 1
    assert result["risk_changes"][0].change_type == RiskChangeType.RESOLVED
    investigator.investigate.assert_called_once()