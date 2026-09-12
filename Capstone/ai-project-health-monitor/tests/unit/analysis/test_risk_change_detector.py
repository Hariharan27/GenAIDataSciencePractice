from datetime import UTC, datetime

from ai_project_health_monitor.analysis.risk_change_detector import (
    RiskChangeDetector,
)
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.risk_change import RiskChangeType
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)


def build_risk_signal(
    signal_id: str,
    event_id: str = "EVT-001",
    risk_type: RiskType = RiskType.BLOCKER,
    severity: RiskSeverity = RiskSeverity.HIGH,
) -> RiskSignal:
    evidence = Evidence(
        event_id=event_id,
        source_type=SourceType.JIRA,
        source_id=f"JIRA-{event_id}",
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
        event_id=event_id,
        risk_type=risk_type,
        severity=severity,
        confidence=0.95,
        evidence=evidence,
        evidence_quote="Payment API integration is blocked.",
        rationale="The payment API integration is blocked.",
    )


def test_detects_new_risk() -> None:
    current = build_risk_signal("CURRENT-001")

    changes = RiskChangeDetector().detect(
        previous_risks=[],
        current_risks=[current],
    )

    assert len(changes) == 1
    assert changes[0].change_type == RiskChangeType.NEW
    assert changes[0].previous_risk is None
    assert changes[0].current_risk == current


def test_detects_resolved_risk() -> None:
    previous = build_risk_signal("PREVIOUS-001")

    changes = RiskChangeDetector().detect(
        previous_risks=[previous],
        current_risks=[],
    )

    assert len(changes) == 1
    assert changes[0].change_type == RiskChangeType.RESOLVED
    assert changes[0].previous_risk == previous
    assert changes[0].current_risk is None


def test_detects_continuing_risk_even_when_signal_id_changes() -> None:
    previous = build_risk_signal(
        signal_id="PREVIOUS-001",
        severity=RiskSeverity.HIGH,
    )
    current = build_risk_signal(
        signal_id="CURRENT-999",
        severity=RiskSeverity.HIGH,
    )

    changes = RiskChangeDetector().detect(
        previous_risks=[previous],
        current_risks=[current],
    )

    assert len(changes) == 1
    assert changes[0].change_type == RiskChangeType.CONTINUING
    assert changes[0].previous_risk == previous
    assert changes[0].current_risk == current


def test_detects_severity_increase() -> None:
    previous = build_risk_signal(
        signal_id="PREVIOUS-001",
        severity=RiskSeverity.HIGH,
    )
    current = build_risk_signal(
        signal_id="CURRENT-001",
        severity=RiskSeverity.CRITICAL,
    )

    changes = RiskChangeDetector().detect(
        previous_risks=[previous],
        current_risks=[current],
    )

    assert len(changes) == 1
    assert changes[0].change_type == RiskChangeType.SEVERITY_INCREASED


def test_detects_severity_decrease() -> None:
    previous = build_risk_signal(
        signal_id="PREVIOUS-001",
        severity=RiskSeverity.CRITICAL,
    )
    current = build_risk_signal(
        signal_id="CURRENT-001",
        severity=RiskSeverity.MEDIUM,
    )

    changes = RiskChangeDetector().detect(
        previous_risks=[previous],
        current_risks=[current],
    )

    assert len(changes) == 1
    assert changes[0].change_type == RiskChangeType.SEVERITY_DECREASED


def test_matches_risks_by_project_event_and_risk_type() -> None:
    previous = build_risk_signal(
        signal_id="PREVIOUS-001",
        event_id="EVT-001",
        risk_type=RiskType.BLOCKER,
    )
    current = build_risk_signal(
        signal_id="CURRENT-001",
        event_id="EVT-001",
        risk_type=RiskType.BLOCKER,
    )

    changes = RiskChangeDetector().detect(
        previous_risks=[previous],
        current_risks=[current],
    )

    assert len(changes) == 1
    assert changes[0].change_type == RiskChangeType.CONTINUING


def test_different_risk_type_is_treated_as_new_and_resolved() -> None:
    previous = build_risk_signal(
        signal_id="PREVIOUS-001",
        risk_type=RiskType.BLOCKER,
    )
    current = build_risk_signal(
        signal_id="CURRENT-001",
        risk_type=RiskType.DELAY,
    )

    changes = RiskChangeDetector().detect(
        previous_risks=[previous],
        current_risks=[current],
    )

    assert len(changes) == 2

    change_types = {change.change_type for change in changes}

    assert RiskChangeType.NEW in change_types
    assert RiskChangeType.RESOLVED in change_types
    