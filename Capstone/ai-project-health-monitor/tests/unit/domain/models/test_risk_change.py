from datetime import UTC, datetime

from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.risk_change import (
    RiskChange,
    RiskChangeType,
)
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)


def build_risk_signal(
    signal_id: str,
    severity: RiskSeverity,
) -> RiskSignal:
    evidence = Evidence(
        event_id="EVT-001",
        source_type=SourceType.JIRA,
        source_id="JIRA-001",
        content="Payment API integration is blocked.",
        occurred_at=datetime(
            2026,
            9,
            1,
            tzinfo=UTC,
        ),
    )

    return RiskSignal(
        signal_id=signal_id,
        project_id="PROJ-001",
        event_id="EVT-001",
        risk_type=RiskType.BLOCKER,
        severity=severity,
        confidence=0.95,
        evidence=evidence,
        evidence_quote="Payment API integration is blocked.",
        rationale="The payment API integration is blocked.",
    )


def test_risk_change_represents_new_risk() -> None:
    current_risk = build_risk_signal(
        signal_id="CURRENT-001",
        severity=RiskSeverity.HIGH,
    )

    change = RiskChange(
        project_id="PROJ-001",
        change_type=RiskChangeType.NEW,
        current_risk=current_risk,
        rationale="A new blocker was detected.",
    )

    assert change.change_type == RiskChangeType.NEW
    assert change.previous_risk is None
    assert change.current_risk == current_risk


def test_risk_change_represents_resolved_risk() -> None:
    previous_risk = build_risk_signal(
        signal_id="PREVIOUS-001",
        severity=RiskSeverity.HIGH,
    )

    change = RiskChange(
        project_id="PROJ-001",
        change_type=RiskChangeType.RESOLVED,
        previous_risk=previous_risk,
        rationale="The previous blocker is no longer present.",
    )

    assert change.change_type == RiskChangeType.RESOLVED
    assert change.previous_risk == previous_risk
    assert change.current_risk is None


def test_risk_change_represents_continuing_risk() -> None:
    previous_risk = build_risk_signal(
        signal_id="PREVIOUS-001",
        severity=RiskSeverity.HIGH,
    )
    current_risk = build_risk_signal(
        signal_id="CURRENT-001",
        severity=RiskSeverity.HIGH,
    )

    change = RiskChange(
        project_id="PROJ-001",
        change_type=RiskChangeType.CONTINUING,
        previous_risk=previous_risk,
        current_risk=current_risk,
        rationale="The blocker remains present.",
    )

    assert change.change_type == RiskChangeType.CONTINUING
    assert change.previous_risk == previous_risk
    assert change.current_risk == current_risk


def test_risk_change_represents_severity_increase() -> None:
    previous_risk = build_risk_signal(
        signal_id="PREVIOUS-001",
        severity=RiskSeverity.HIGH,
    )
    current_risk = build_risk_signal(
        signal_id="CURRENT-001",
        severity=RiskSeverity.CRITICAL,
    )

    change = RiskChange(
        project_id="PROJ-001",
        change_type=RiskChangeType.SEVERITY_INCREASED,
        previous_risk=previous_risk,
        current_risk=current_risk,
        rationale="The blocker increased from high to critical.",
    )

    assert change.change_type == RiskChangeType.SEVERITY_INCREASED
    assert change.previous_risk.severity == RiskSeverity.HIGH
    assert change.current_risk.severity == RiskSeverity.CRITICAL


def test_risk_change_represents_severity_decrease() -> None:
    previous_risk = build_risk_signal(
        signal_id="PREVIOUS-001",
        severity=RiskSeverity.CRITICAL,
    )
    current_risk = build_risk_signal(
        signal_id="CURRENT-001",
        severity=RiskSeverity.MEDIUM,
    )

    change = RiskChange(
        project_id="PROJ-001",
        change_type=RiskChangeType.SEVERITY_DECREASED,
        previous_risk=previous_risk,
        current_risk=current_risk,
        rationale="The blocker decreased from critical to medium.",
    )

    assert change.change_type == RiskChangeType.SEVERITY_DECREASED
    assert change.previous_risk.severity == RiskSeverity.CRITICAL
    assert change.current_risk.severity == RiskSeverity.MEDIUM