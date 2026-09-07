import pytest
from pydantic import ValidationError

from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)


def test_risk_signal_creation() -> None:
    evidence = Evidence(
        event_id="EVT-JIRA-001",
        source_type="jira",
        source_id="JIRA-101",
        content="Backend integration is blocked by the payment API.",
        occurred_at="2026-09-03T10:30:00Z",
    )

    signal = RiskSignal(
        signal_id="RISK-001",
        project_id="PROJ-001",
        event_id="EVT-001",
        risk_type=RiskType.BLOCKER,
        severity=RiskSeverity.HIGH,
        confidence=0.91,
        evidence=evidence,
        evidence_quote=evidence.content,
        rationale="The dependency is preventing completion of the integration task.",
    )

    assert signal.risk_type == RiskType.BLOCKER
    assert signal.severity == RiskSeverity.HIGH
    assert signal.confidence == 0.91
    assert signal.evidence.source_type == "jira"
    assert signal.evidence.source_id == "JIRA-101"


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_confidence_must_be_between_zero_and_one(
    confidence: float,
) -> None:
    evidence = Evidence(
        event_id="EVT-JIRA-101",
        source_type="jira",
        source_id="JIRA-101",
        content="The delivery is delayed.",
        occurred_at="2026-09-03T10:30:00Z",
    )

    with pytest.raises(ValidationError):
        RiskSignal(
            signal_id="RISK-001",
            project_id="PROJ-001",
            event_id="EVT-001",
            risk_type=RiskType.DELAY,
            severity=RiskSeverity.MEDIUM,
            confidence=confidence,
            evidence=evidence,
            evidence_quote=evidence.content,
            rationale="The planned delivery date has been missed.",
        )


def test_risk_signal_rejects_unknown_risk_type() -> None:
    evidence = Evidence(
        event_id="EVT-DOC-001",
        source_type="document",
        source_id="DOC-001",
        content="Something may be wrong.",
        occurred_at="2026-09-03T10:30:00Z",
    )

    with pytest.raises(ValidationError):
        RiskSignal(
            signal_id="RISK-001",
            project_id="PROJ-001",
            event_id="EVT-001",
            risk_type="unknown",
            severity=RiskSeverity.LOW,
            confidence=0.5,
            evidence=evidence,
            evidence_quote=evidence.content,
            rationale="The source contains an unclear warning.",
        )


def test_risk_signal_rejects_invalid_evidence() -> None:
    with pytest.raises(ValidationError):
        RiskSignal(
            signal_id="RISK-001",
            project_id="PROJ-001",
            event_id="EVT-001",
            risk_type=RiskType.DELAY,
            severity=RiskSeverity.HIGH,
            confidence=0.8,
            evidence="",
            evidence_quote="",
            rationale="The delivery appears to be delayed.",
        )