from datetime import UTC, datetime

import pytest

from ai_project_health_monitor.analysis.deterministic_health_scorer import (
    DeterministicHealthScorer,
)
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)


@pytest.fixture
def scorer() -> DeterministicHealthScorer:
    return DeterministicHealthScorer()


@pytest.fixture
def evidence() -> Evidence:
    return Evidence(
        event_id="EVT-JIRA-001",
        source_type=SourceType.JIRA,
        source_id="EVT-JIRA-001",
        content="Payment API integration is blocked.",
        occurred_at=datetime(
            2026,
            9,
            1,
            tzinfo=UTC,
        ),
    )


def make_risk_signal(
    evidence: Evidence,
    *,
    signal_id: str,
    severity: RiskSeverity,
    confidence: float,
    risk_type: RiskType = RiskType.BLOCKER,
) -> RiskSignal:
    return RiskSignal(
        signal_id=signal_id,
        project_id="PROJ-001",
        event_id=evidence.source_id,
        risk_type=risk_type,
        severity=severity,
        confidence=confidence,
        evidence=evidence,
        evidence_quote=evidence.content,
        rationale="Risk is supported by project evidence.",
    )


def test_calculate_returns_healthy_score_without_risks(
    scorer: DeterministicHealthScorer,
) -> None:
    result = scorer.calculate(
        project_id="PROJ-001",
        risk_signals=[],
    )

    assert result.score == 100.0
    assert result.status == HealthStatus.HEALTHY
    assert result.contributing_risks == []
    assert "no detected risks" in result.rationale


def test_calculate_applies_severity_and_confidence(
    scorer: DeterministicHealthScorer,
    evidence: Evidence,
) -> None:
    signals = [
        make_risk_signal(
            evidence,
            signal_id="RISK-001",
            severity=RiskSeverity.HIGH,
            confidence=0.8,
        )
    ]

    result = scorer.calculate(
        project_id="PROJ-001",
        risk_signals=signals,
    )

    # HIGH = 20 penalty × 0.8 confidence = 16 penalty.
    assert result.score == 84.0
    assert result.status == HealthStatus.HEALTHY
    assert result.contributing_risks == ["RISK-001"]


def test_calculate_classifies_at_risk(
    scorer: DeterministicHealthScorer,
    evidence: Evidence,
) -> None:
    signals = [
        make_risk_signal(
            evidence,
            signal_id="RISK-001",
            severity=RiskSeverity.CRITICAL,
            confidence=1.0,
        )
    ]

    result = scorer.calculate(
        project_id="PROJ-001",
        risk_signals=signals,
    )

    assert result.score == 65.0
    assert result.status == HealthStatus.AT_RISK


def test_calculate_remains_at_risk_above_critical_threshold(
    scorer: DeterministicHealthScorer,
    evidence: Evidence,
) -> None:
    signals = [
        make_risk_signal(
            evidence,
            signal_id="RISK-001",
            severity=RiskSeverity.CRITICAL,
            confidence=1.0,
        ),
        make_risk_signal(
            evidence,
            signal_id="RISK-002",
            severity=RiskSeverity.HIGH,
            confidence=1.0,
        ),
    ]

    result = scorer.calculate(
        project_id="PROJ-001",
        risk_signals=signals,
    )

    # 100 - 35 - 20 = 45, still AT_RISK.
    assert result.score == 45.0
    assert result.status == HealthStatus.AT_RISK


def test_calculate_clamps_score_at_zero(
    scorer: DeterministicHealthScorer,
    evidence: Evidence,
) -> None:
    signals = [
        make_risk_signal(
            evidence,
            signal_id=f"RISK-{index}",
            severity=RiskSeverity.CRITICAL,
            confidence=1.0,
        )
        for index in range(4)
    ]

    result = scorer.calculate(
        project_id="PROJ-001",
        risk_signals=signals,
    )

    assert result.score == 0.0
    assert result.status == HealthStatus.CRITICAL


def test_calculate_supports_multiple_severity_levels(
    scorer: DeterministicHealthScorer,
    evidence: Evidence,
) -> None:
    signals = [
        make_risk_signal(
            evidence,
            signal_id="RISK-LOW",
            severity=RiskSeverity.LOW,
            confidence=1.0,
        ),
        make_risk_signal(
            evidence,
            signal_id="RISK-MEDIUM",
            severity=RiskSeverity.MEDIUM,
            confidence=1.0,
        ),
        make_risk_signal(
            evidence,
            signal_id="RISK-HIGH",
            severity=RiskSeverity.HIGH,
            confidence=1.0,
        ),
    ]

    result = scorer.calculate(
        project_id="PROJ-001",
        risk_signals=signals,
    )

    # 100 - 5 - 10 - 20 = 65.
    assert result.score == 65.0
    assert result.status == HealthStatus.AT_RISK


def test_calculate_rejects_empty_project_id(
    scorer: DeterministicHealthScorer,
) -> None:
    with pytest.raises(
        ValueError,
        match="project_id cannot be empty",
    ):
        scorer.calculate(
            project_id="   ",
            risk_signals=[],
        )


def test_calculate_includes_risk_details_in_rationale(
    scorer: DeterministicHealthScorer,
    evidence: Evidence,
) -> None:
    signals = [
        make_risk_signal(
            evidence,
            signal_id="RISK-001",
            severity=RiskSeverity.HIGH,
            confidence=1.0,
            risk_type=RiskType.DELAY,
        )
    ]

    result = scorer.calculate(
        project_id="PROJ-001",
        risk_signals=signals,
    )

    assert "delay" in result.rationale
    assert "high" in result.rationale
    assert "80.0/100" in result.rationale


def test_calculate_classifies_exactly_thirty_critical(
    scorer: DeterministicHealthScorer,
    evidence: Evidence,
) -> None:
    signals = [
        make_risk_signal(
            evidence,
            signal_id="RISK-CRITICAL",
            severity=RiskSeverity.CRITICAL,
            confidence=1.0,
        ),
        make_risk_signal(
            evidence,
            signal_id="RISK-HIGH",
            severity=RiskSeverity.HIGH,
            confidence=1.0,
        ),
        make_risk_signal(
            evidence,
            signal_id="RISK-MEDIUM",
            severity=RiskSeverity.MEDIUM,
            confidence=1.0,
        ),
        make_risk_signal(
            evidence,
            signal_id="RISK-LOW",
            severity=RiskSeverity.LOW,
            confidence=1.0,
        ),
    ]

    result = scorer.calculate(
        project_id="PROJ-001",
        risk_signals=signals,
    )

    assert result.score == 30.0
    assert result.status == HealthStatus.CRITICAL


def test_calculate_keeps_exactly_seventy_healthy(
    scorer: DeterministicHealthScorer,
    evidence: Evidence,
) -> None:
    signals = [
        make_risk_signal(
            evidence,
            signal_id="RISK-HIGH",
            severity=RiskSeverity.HIGH,
            confidence=1.0,
        ),
        make_risk_signal(
            evidence,
            signal_id="RISK-MEDIUM",
            severity=RiskSeverity.MEDIUM,
            confidence=1.0,
        ),
    ]

    result = scorer.calculate(
        project_id="PROJ-001",
        risk_signals=signals,
    )

    assert result.score == 70.0
    assert result.status == HealthStatus.HEALTHY


def test_calculate_keeps_exactly_forty_at_risk(
    scorer: DeterministicHealthScorer,
    evidence: Evidence,
) -> None:
    signals = [
        make_risk_signal(
            evidence,
            signal_id="RISK-CRITICAL",
            severity=RiskSeverity.CRITICAL,
            confidence=1.0,
        ),
        make_risk_signal(
            evidence,
            signal_id="RISK-HIGH",
            severity=RiskSeverity.HIGH,
            confidence=1.0,
        ),
        make_risk_signal(
            evidence,
            signal_id="RISK-LOW",
            severity=RiskSeverity.LOW,
            confidence=1.0,
        ),
    ]

    result = scorer.calculate(
        project_id="PROJ-001",
        risk_signals=signals,
    )

    assert result.score == 40.0
    assert result.status == HealthStatus.AT_RISK