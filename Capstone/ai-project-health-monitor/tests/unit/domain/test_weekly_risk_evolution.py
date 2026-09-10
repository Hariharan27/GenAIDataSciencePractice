from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)
from ai_project_health_monitor.domain.models.weekly_risk_evolution import (
    RiskEvolutionStatus,
    WeeklyRiskEvolution,
)


def create_risk_signal() -> RiskSignal:
    evidence = Evidence(
        event_id="EVT-JIRA-001",
        source_type="jira",
        source_id="JIRA-101",
        content="Backend integration is blocked by the payment API.",
        occurred_at="2026-09-03T10:30:00Z",
    )

    return RiskSignal(
        signal_id="RISK-001",
        project_id="PROJ-001",
        event_id="EVT-001",
        risk_type=RiskType.BLOCKER,
        severity=RiskSeverity.HIGH,
        confidence=0.95,
        evidence=evidence,
        evidence_quote=evidence.content,
        rationale="The payment API dependency is blocking integration.",
    )


def test_weekly_risk_evolution_represents_new_risk() -> None:
    risk = create_risk_signal()

    evolution = WeeklyRiskEvolution(
        risk=risk,
        status=RiskEvolutionStatus.NEW,
        first_seen=True,
        last_seen=True,
    )

    assert evolution.risk == risk
    assert evolution.status == RiskEvolutionStatus.NEW
    assert evolution.first_seen is True
    assert evolution.last_seen is True


def test_weekly_risk_evolution_represents_persisting_risk() -> None:
    risk = create_risk_signal()

    evolution = WeeklyRiskEvolution(
        risk=risk,
        status=RiskEvolutionStatus.PERSISTING,
        first_seen=False,
        last_seen=True,
    )

    assert evolution.risk == risk
    assert evolution.status == RiskEvolutionStatus.PERSISTING
    assert evolution.first_seen is False
    assert evolution.last_seen is True


def test_weekly_risk_evolution_represents_resolved_risk() -> None:
    risk = create_risk_signal()

    evolution = WeeklyRiskEvolution(
        risk=risk,
        status=RiskEvolutionStatus.RESOLVED,
        first_seen=True,
        last_seen=False,
    )

    assert evolution.risk == risk
    assert evolution.status == RiskEvolutionStatus.RESOLVED
    assert evolution.first_seen is True
    assert evolution.last_seen is False