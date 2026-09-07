from datetime import UTC, datetime

from ai_project_health_monitor.analysis.risk_consolidator import RiskConsolidator
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)


def build_signal(
    signal_id: str,
    risk_type: RiskType,
    event_id: str,
) -> RiskSignal:
    evidence = Evidence(
        event_id=event_id,
        source_type=SourceType.JIRA,
        source_id=event_id,
        content=f"Evidence for {risk_type.value}",
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
        severity=RiskSeverity.HIGH,
        confidence=0.9,
        evidence=evidence,
        evidence_quote=evidence.content,
        rationale=f"Rationale for {risk_type.value}",
    )


def test_consolidates_dependency_when_it_shares_event_with_primary() -> None:
    signals = [
        build_signal(
            "SIG-001",
            RiskType.BLOCKER,
            "EVT-001",
        ),
        build_signal(
            "SIG-002",
            RiskType.DEPENDENCY,
            "EVT-001",
        ),
    ]

    groups = RiskConsolidator().consolidate(signals)

    assert len(groups) == 1

    group = groups[0]

    assert group.primary_risk.risk_type == RiskType.BLOCKER

    assert [
        signal.risk_type
        for signal in group.contributing_risks
    ] == [
        RiskType.DEPENDENCY
    ]

    assert group.impact_risks == []


def test_delay_remains_independently_scoreable() -> None:
    signals = [
        build_signal(
            "SIG-001",
            RiskType.BLOCKER,
            "EVT-001",
        ),
        build_signal(
            "SIG-002",
            RiskType.DELAY,
            "EVT-002",
        ),
    ]

    groups = RiskConsolidator().consolidate(signals)

    assert len(groups) == 2

    assert [
        group.primary_risk.risk_type
        for group in groups
    ] == [
        RiskType.BLOCKER,
        RiskType.DELAY,
    ]


def test_dependency_from_different_event_remains_independently_scoreable() -> None:
    signals = [
        build_signal(
            "SIG-001",
            RiskType.BLOCKER,
            "EVT-001",
        ),
        build_signal(
            "SIG-002",
            RiskType.DEPENDENCY,
            "EVT-002",
        ),
    ]

    groups = RiskConsolidator().consolidate(signals)

    assert len(groups) == 1

    group = groups[0]

    assert group.primary_risk.risk_type == RiskType.BLOCKER
    assert group.contributing_risks == []


def test_scope_creep_remains_primary_risk() -> None:
    signals = [
        build_signal(
            "SIG-001",
            RiskType.SCOPE_CREEP,
            "EVT-001",
        )
    ]

    groups = RiskConsolidator().consolidate(signals)

    assert len(groups) == 1
    assert groups[0].primary_risk.risk_type == RiskType.SCOPE_CREEP
    assert groups[0].contributing_risks == []
    assert groups[0].impact_risks == []


def test_returns_empty_for_empty_signals() -> None:
    groups = RiskConsolidator().consolidate([])

    assert groups == []


def test_primary_risks_returns_only_primary_risks() -> None:
    signals = [
        build_signal(
            "SIG-001",
            RiskType.BLOCKER,
            "EVT-001",
        ),
        build_signal(
            "SIG-002",
            RiskType.DEPENDENCY,
            "EVT-001",
        ),
        build_signal(
            "SIG-003",
            RiskType.DELAY,
            "EVT-002",
        ),
    ]

    consolidator = RiskConsolidator()

    groups = consolidator.consolidate(signals)
    primary_risks = consolidator.primary_risks(groups)

    assert len(primary_risks) == 2

    assert [
        signal.risk_type
        for signal in primary_risks
    ] == [
        RiskType.BLOCKER,
        RiskType.DELAY,
    ]