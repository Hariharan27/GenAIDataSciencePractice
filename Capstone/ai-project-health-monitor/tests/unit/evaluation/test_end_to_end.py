from datetime import UTC, datetime

import pytest

from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)
from ai_project_health_monitor.evaluation.end_to_end import EndToEndEvaluator
from ai_project_health_monitor.evaluation.models.end_to_end import (
    EndToEndEvaluationCase,
)


def make_signal(
    project_id: str,
    risk_type: RiskType,
    severity: RiskSeverity,
    confidence: float,
) -> RiskSignal:
    evidence = Evidence(
        event_id="EVT-TEST-001",
        source_type=SourceType.JIRA,
        source_id="EVT-TEST-001",
        content="Synthetic evaluation evidence.",
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    return RiskSignal(
        signal_id="RISK-TEST-001",
        project_id=project_id,
        event_id=evidence.event_id,
        risk_type=risk_type,
        severity=severity,
        confidence=confidence,
        evidence=evidence,
        rationale="Synthetic evaluation risk.",
    )


def test_evaluate_case_passes_when_pipeline_matches_expected() -> None:
    def analyze(
        project_id: str,
        risk_signals: list[RiskSignal],
    ):
        from ai_project_health_monitor.analysis.deterministic_health_scorer import (
            DeterministicHealthScorer,
        )

        return DeterministicHealthScorer().calculate(
            project_id,
            risk_signals,
        )

    evaluator = EndToEndEvaluator(analyze)

    case = EndToEndEvaluationCase(
        case_id="E2E-TEST-001",
        project_id="PROJ-001",
        query="What risks are affecting the project?",
        expected_risk_types=[RiskType.BLOCKER],
        expected_status=HealthStatus.AT_RISK,
        min_expected_score=60.0,
        max_expected_score=70.0,
    )

    signals = [
        make_signal(
            "PROJ-001",
            RiskType.BLOCKER,
            RiskSeverity.CRITICAL,
            1.0,
        )
    ]

    result = evaluator.evaluate_case(case, signals)

    assert result.risk_detection_correct is True
    assert result.status_correct is True
    assert result.score_in_range is True


def test_evaluate_case_detects_wrong_risk() -> None:
    def analyze(
        project_id: str,
        risk_signals: list[RiskSignal],
    ):
        from ai_project_health_monitor.analysis.deterministic_health_scorer import (
            DeterministicHealthScorer,
        )

        return DeterministicHealthScorer().calculate(
            project_id,
            risk_signals,
        )

    evaluator = EndToEndEvaluator(analyze)

    case = EndToEndEvaluationCase(
        case_id="E2E-TEST-002",
        project_id="PROJ-001",
        query="What risks are affecting the project?",
        expected_risk_types=[RiskType.DELAY],
        expected_status=HealthStatus.HEALTHY,
        min_expected_score=70.0,
        max_expected_score=100.0,
    )

    signals = [
        make_signal(
            "PROJ-001",
            RiskType.BLOCKER,
            RiskSeverity.LOW,
            1.0,
        )
    ]

    result = evaluator.evaluate_case(case, signals)

    assert result.risk_detection_correct is False
    assert result.status_correct is True
    assert result.score_in_range is True


def test_evaluate_handles_empty_cases() -> None:
    evaluator = EndToEndEvaluator(
        lambda project_id, risk_signals: None
    )

    run = evaluator.evaluate(
        cases=[],
        risk_signals_by_case={},
    )

    assert run.summary.total_cases == 0
    assert run.summary.risk_detection_accuracy == 0.0
    assert run.summary.status_accuracy == 0.0
    assert run.summary.score_range_accuracy == 0.0
    assert run.results == []

def test_evaluate_case_calculates_false_positives() -> None:
    from ai_project_health_monitor.analysis.deterministic_health_scorer import (
        DeterministicHealthScorer,
    )

    evaluator = EndToEndEvaluator(
        DeterministicHealthScorer().calculate
    )

    case = EndToEndEvaluationCase(
        case_id="E2E-TEST-003",
        project_id="PROJ-001",
        query="What risks are affecting the project?",
        expected_risk_types=[
            RiskType.BLOCKER,
            RiskType.DELAY,
        ],
        expected_status=HealthStatus.HEALTHY,
        min_expected_score=0.0,
        max_expected_score=100.0,
    )

    signals = [
        make_signal(
            "PROJ-001",
            RiskType.BLOCKER,
            RiskSeverity.LOW,
            1.0,
        ),
        make_signal(
            "PROJ-001",
            RiskType.DELAY,
            RiskSeverity.LOW,
            1.0,
        ),
        make_signal(
            "PROJ-001",
            RiskType.DEPENDENCY,
            RiskSeverity.LOW,
            1.0,
        ),
    ]

    result = evaluator.evaluate_case(case, signals)

    assert result.true_positive_count == 2
    assert result.false_positive_count == 1
    assert result.false_negative_count == 0

    assert result.risk_precision == pytest.approx(2 / 3)
    assert result.risk_recall == 1.0
    assert result.risk_f1 == pytest.approx(0.8)

def test_evaluate_case_calculates_false_negatives() -> None:
    from ai_project_health_monitor.analysis.deterministic_health_scorer import (
        DeterministicHealthScorer,
    )

    evaluator = EndToEndEvaluator(
        DeterministicHealthScorer().calculate
    )

    case = EndToEndEvaluationCase(
        case_id="E2E-TEST-004",
        project_id="PROJ-001",
        query="What risks are affecting the project?",
        expected_risk_types=[
            RiskType.BLOCKER,
            RiskType.DELAY,
        ],
        expected_status=HealthStatus.HEALTHY,
        min_expected_score=0.0,
        max_expected_score=100.0,
    )

    signals = [
        make_signal(
            "PROJ-001",
            RiskType.BLOCKER,
            RiskSeverity.LOW,
            1.0,
        )
    ]

    result = evaluator.evaluate_case(case, signals)

    assert result.true_positive_count == 1
    assert result.false_positive_count == 0
    assert result.false_negative_count == 1

    assert result.risk_precision == 1.0
    assert result.risk_recall == pytest.approx(0.5)
    assert result.risk_f1 == pytest.approx(2 / 3)


def test_evaluate_case_handles_no_expected_and_no_predicted_risks() -> None:
    from ai_project_health_monitor.analysis.deterministic_health_scorer import (
        DeterministicHealthScorer,
    )

    evaluator = EndToEndEvaluator(
        DeterministicHealthScorer().calculate
    )

    case = EndToEndEvaluationCase(
        case_id="E2E-TEST-005",
        project_id="PROJ-002",
        query="Are there any risks?",
        expected_risk_types=[],
        expected_status=HealthStatus.HEALTHY,
        min_expected_score=90.0,
        max_expected_score=100.0,
    )

    result = evaluator.evaluate_case(case, [])

    assert result.true_positive_count == 0
    assert result.false_positive_count == 0
    assert result.false_negative_count == 0

    assert result.risk_precision == 1.0
    assert result.risk_recall == 1.0
    assert result.risk_f1 == 1.0