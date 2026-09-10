from datetime import datetime, timedelta

from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)
from ai_project_health_monitor.domain.models.weekly_health_history import (
    HealthHistoryPoint,
    WeeklyHealthHistory,
)
from ai_project_health_monitor.domain.models.weekly_risk_evolution import (
    RiskEvolutionStatus,
)
from ai_project_health_monitor.services.weekly_risk_evolution_service import (
    WeeklyRiskEvolutionService,
)


def create_risk_signal(
    *,
    signal_id: str,
    event_id: str,
    risk_type: RiskType,
) -> RiskSignal:
    evidence = Evidence(
        event_id=event_id,
        source_type="jira",
        source_id=event_id,
        content="Project risk evidence.",
        occurred_at="2026-09-03T10:30:00Z",
    )

    return RiskSignal(
        signal_id=signal_id,
        project_id="PROJ-001",
        event_id=event_id,
        risk_type=risk_type,
        severity=RiskSeverity.HIGH,
        confidence=0.95,
        evidence=evidence,
        evidence_quote=evidence.content,
        rationale="The project contains an explicit risk.",
    )


def create_history(
    *,
    first_time: datetime,
    first_risks: list[RiskSignal],
    latest_risks: list[RiskSignal],
) -> WeeklyHealthHistory:
    return WeeklyHealthHistory(
        project_id="PROJ-001",
        start_date=first_time,
        end_date=first_time + timedelta(days=2),
        snapshots=[
            HealthHistoryPoint(
                calculated_at=first_time,
                health_score=70.0,
                health_status=HealthStatus.AT_RISK,
                risk_signals=first_risks,
            ),
            HealthHistoryPoint(
                calculated_at=first_time + timedelta(days=2),
                health_score=70.0,
                health_status=HealthStatus.AT_RISK,
                risk_signals=latest_risks,
            ),
        ],
    )


def test_analyze_marks_risk_as_persisting() -> None:
    service = WeeklyRiskEvolutionService()

    risk = create_risk_signal(
        signal_id="RISK-001",
        event_id="EVT-001",
        risk_type=RiskType.BLOCKER,
    )

    first_time = datetime(2026, 9, 1, 10, 0, 0)

    history = create_history(
        first_time=first_time,
        first_risks=[risk],
        latest_risks=[risk],
    )

    evolution = service.analyze(history)

    assert len(evolution) == 1
    assert evolution[0].status == RiskEvolutionStatus.PERSISTING
    assert evolution[0].risk.risk_type == RiskType.BLOCKER
    assert evolution[0].first_seen is False
    assert evolution[0].last_seen is True


def test_analyze_marks_new_risk() -> None:
    service = WeeklyRiskEvolutionService()

    blocker = create_risk_signal(
        signal_id="RISK-001",
        event_id="EVT-001",
        risk_type=RiskType.BLOCKER,
    )

    delay = create_risk_signal(
        signal_id="RISK-002",
        event_id="EVT-002",
        risk_type=RiskType.DELAY,
    )

    first_time = datetime(2026, 9, 1, 10, 0, 0)

    history = create_history(
        first_time=first_time,
        first_risks=[blocker],
        latest_risks=[blocker, delay],
    )

    evolution = service.analyze(history)

    assert len(evolution) == 2

    persisting = [
        item for item in evolution if item.risk.risk_type == RiskType.BLOCKER
    ]

    new = [
        item for item in evolution if item.risk.risk_type == RiskType.DELAY
    ]

    assert len(persisting) == 1
    assert persisting[0].status == RiskEvolutionStatus.PERSISTING

    assert len(new) == 1
    assert new[0].status == RiskEvolutionStatus.NEW
    assert new[0].first_seen is True
    assert new[0].last_seen is True


def test_analyze_marks_missing_latest_risk_as_resolved() -> None:
    service = WeeklyRiskEvolutionService()

    risk = create_risk_signal(
        signal_id="RISK-001",
        event_id="EVT-001",
        risk_type=RiskType.BLOCKER,
    )

    first_time = datetime(2026, 9, 1, 10, 0, 0)

    history = create_history(
        first_time=first_time,
        first_risks=[risk],
        latest_risks=[],
    )

    evolution = service.analyze(history)

    assert len(evolution) == 1
    assert evolution[0].status == RiskEvolutionStatus.RESOLVED
    assert evolution[0].risk.risk_type == RiskType.BLOCKER
    assert evolution[0].first_seen is True
    assert evolution[0].last_seen is False


def test_analyze_returns_empty_list_when_no_snapshots_exist() -> None:
    service = WeeklyRiskEvolutionService()

    history = WeeklyHealthHistory(
        project_id="PROJ-001",
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 3),
        snapshots=[],
    )

    evolution = service.analyze(history)

    assert evolution == []