from datetime import UTC, datetime

import pytest

from ai_project_health_monitor.analysis.deterministic_health_scorer import (
    DeterministicHealthScorer,
)
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)
from ai_project_health_monitor.evaluation.health import HealthEvaluator
from ai_project_health_monitor.evaluation.models.health import (
    HealthEvaluationCase,
    HealthEvaluationRisk,
)


@pytest.fixture
def scorer() -> DeterministicHealthScorer:
    return DeterministicHealthScorer()


@pytest.fixture
def evaluator(
    scorer: DeterministicHealthScorer,
) -> HealthEvaluator:
    return HealthEvaluator(scorer.calculate)


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
) -> RiskSignal:
    return RiskSignal(
        signal_id=signal_id,
        project_id="PROJ-001",
        event_id=evidence.event_id,
        risk_type=RiskType.BLOCKER,
        severity=severity,
        confidence=confidence,
        evidence=evidence,
        evidence_quote=evidence.content,
        rationale="Risk is supported by project evidence.",
    )


def test_evaluate_case_marks_correct_score_and_status(
    evaluator: HealthEvaluator,
    evidence: Evidence,
) -> None:
    case = HealthEvaluationCase(
        case_id="HEALTH-001",
        project_id="PROJ-001",
        risks=[
            HealthEvaluationRisk(
                severity=RiskSeverity.HIGH,
                confidence=0.8,
            )
        ],
        expected_score=84.0,
        expected_status="healthy",
    )

    signals = [
        make_risk_signal(
            evidence,
            signal_id="RISK-001",
            severity=RiskSeverity.HIGH,
            confidence=0.8,
        )
    ]

    result = evaluator.evaluate_case(case, signals)

    assert result.score_correct is True
    assert result.status_correct is True
    assert result.predicted_score == 84.0


def test_evaluate_case_detects_wrong_expected_score(
    evaluator: HealthEvaluator,
    evidence: Evidence,
) -> None:
    case = HealthEvaluationCase(
        case_id="HEALTH-002",
        project_id="PROJ-001",
        risks=[],
        expected_score=90.0,
        expected_status="healthy",
    )

    result = evaluator.evaluate_case(case, [])

    assert result.score_correct is False
    assert result.status_correct is True
    assert result.predicted_score == 100.0


def test_evaluate_case_detects_wrong_expected_status(
    evaluator: HealthEvaluator,
    evidence: Evidence,
) -> None:
    case = HealthEvaluationCase(
        case_id="HEALTH-003",
        project_id="PROJ-001",
        risks=[],
        expected_score=100.0,
        expected_status="at_risk",
    )

    result = evaluator.evaluate_case(case, [])

    assert result.score_correct is True
    assert result.status_correct is False
    assert result.predicted_score == 100.0


def test_evaluate_aggregates_metrics(
    evaluator: HealthEvaluator,
    evidence: Evidence,
) -> None:
    cases = [
        HealthEvaluationCase(
            case_id="HEALTH-001",
            project_id="PROJ-001",
            risks=[],
            expected_score=100.0,
            expected_status="healthy",
        ),
        HealthEvaluationCase(
            case_id="HEALTH-002",
            project_id="PROJ-001",
            risks=[],
            expected_score=90.0,
            expected_status="healthy",
        ),
    ]

    run = evaluator.evaluate(
        cases,
        risk_signals_by_case={},
    )

    assert run.summary.total_cases == 2
    assert run.summary.score_accuracy == 0.5
    assert run.summary.status_accuracy == 1.0


def test_evaluate_handles_empty_cases(
    evaluator: HealthEvaluator,
) -> None:
    run = evaluator.evaluate(
        cases=[],
        risk_signals_by_case={},
    )

    assert run.summary.total_cases == 0
    assert run.summary.score_accuracy == 0.0
    assert run.summary.status_accuracy == 0.0
    assert run.results == []