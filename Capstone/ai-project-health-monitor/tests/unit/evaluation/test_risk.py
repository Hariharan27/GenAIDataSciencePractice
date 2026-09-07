from datetime import UTC, datetime
from unittest.mock import Mock

from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)
from ai_project_health_monitor.evaluation.models.risk import (
    RiskEvaluationCase,
)
from ai_project_health_monitor.evaluation.risk import RiskEvaluator


def _evidence() -> list[Evidence]:
    return [
        Evidence(
            event_id="EVT-JIRA-001",
            source_type=SourceType.JIRA,
            source_id="EVT-JIRA-001",
            content="Payment API integration is blocked.",
            occurred_at=datetime(2026, 9, 1, tzinfo=UTC),
        )
    ]


def _risk_signal(
    risk_type: RiskType = RiskType.BLOCKER,
    severity: RiskSeverity = RiskSeverity.HIGH,
    event_id: str = "EVT-JIRA-001",
) -> RiskSignal:
    return RiskSignal(
        signal_id="RISK-001",
        project_id="PROJ-001",
        event_id=event_id,
        risk_type=risk_type,
        severity=severity,
        confidence=0.9,
        evidence=_evidence()[0],
        evidence_quote=_evidence()[0].content,
        rationale="Payment API integration is blocked.",
    )


def test_evaluate_case_detects_true_positive() -> None:
    analyzer = Mock()
    analyzer.return_value = [_risk_signal()]

    evaluator = RiskEvaluator(analyze=analyzer)

    case = RiskEvaluationCase(
        case_id="RISK-001",
        project_id="PROJ-001",
        evidence_event_ids=["EVT-JIRA-001"],
        expected_risk_types=[RiskType.BLOCKER],
        expected_severities=[RiskSeverity.HIGH],
        expected_evidence_event_ids=["EVT-JIRA-001"],
    )

    result = evaluator.evaluate_case(
        case=case,
        evidence=_evidence(),
    )

    assert result.true_positive_count == 1
    assert result.false_positive_count == 0
    assert result.false_negative_count == 0
    assert result.severity_correct is True
    assert result.evidence_correct is True


def test_evaluate_case_detects_false_positive() -> None:
    analyzer = Mock()
    analyzer.return_value = [_risk_signal(RiskType.DELAY)]

    evaluator = RiskEvaluator(analyze=analyzer)

    case = RiskEvaluationCase(
        case_id="RISK-002",
        project_id="PROJ-001",
        evidence_event_ids=["EVT-JIRA-001"],
        expected_risk_types=[RiskType.BLOCKER],
        expected_severities=[RiskSeverity.HIGH],
        expected_evidence_event_ids=["EVT-JIRA-001"],
    )

    result = evaluator.evaluate_case(
        case=case,
        evidence=_evidence(),
    )

    assert result.true_positive_count == 0
    assert result.false_positive_count == 1
    assert result.false_negative_count == 1
    assert result.severity_correct is True
    assert result.evidence_correct is True


def test_evaluate_case_detects_no_risk_correctly() -> None:
    analyzer = Mock()
    analyzer.return_value = []

    evaluator = RiskEvaluator(analyze=analyzer)

    case = RiskEvaluationCase(
        case_id="RISK-003",
        project_id="PROJ-001",
        evidence_event_ids=["EVT-JIRA-001"],
        expected_risk_types=[],
        expected_severities=[],
        expected_evidence_event_ids=[],
    )

    result = evaluator.evaluate_case(
        case=case,
        evidence=_evidence(),
    )

    assert result.true_positive_count == 0
    assert result.false_positive_count == 0
    assert result.false_negative_count == 0
    assert result.severity_correct is True
    assert result.evidence_correct is True


def test_evaluate_case_detects_incorrect_severity() -> None:
    analyzer = Mock()
    analyzer.return_value = [
        _risk_signal(
            severity=RiskSeverity.MEDIUM,
        )
    ]

    evaluator = RiskEvaluator(analyze=analyzer)

    case = RiskEvaluationCase(
        case_id="RISK-004",
        project_id="PROJ-001",
        evidence_event_ids=["EVT-JIRA-001"],
        expected_risk_types=[RiskType.BLOCKER],
        expected_severities=[RiskSeverity.HIGH],
        expected_evidence_event_ids=["EVT-JIRA-001"],
    )

    result = evaluator.evaluate_case(
        case=case,
        evidence=_evidence(),
    )

    assert result.true_positive_count == 1
    assert result.severity_correct is False
    assert result.evidence_correct is True


def test_evaluate_case_detects_incorrect_evidence() -> None:
    analyzer = Mock()
    analyzer.return_value = [
        _risk_signal(
            event_id="EVT-JIRA-999",
        )
    ]

    evaluator = RiskEvaluator(analyze=analyzer)

    case = RiskEvaluationCase(
        case_id="RISK-005",
        project_id="PROJ-001",
        evidence_event_ids=["EVT-JIRA-001"],
        expected_risk_types=[RiskType.BLOCKER],
        expected_severities=[RiskSeverity.HIGH],
        expected_evidence_event_ids=["EVT-JIRA-001"],
    )

    result = evaluator.evaluate_case(
        case=case,
        evidence=_evidence(),
    )

    assert result.true_positive_count == 1
    assert result.severity_correct is True
    assert result.evidence_correct is False


def test_evaluate_calculates_metrics() -> None:
    analyzer = Mock()
    analyzer.side_effect = [
        [_risk_signal()],
        [_risk_signal(RiskType.DELAY)],
    ]

    evaluator = RiskEvaluator(analyze=analyzer)

    cases = [
        RiskEvaluationCase(
            case_id="RISK-006",
            project_id="PROJ-001",
            evidence_event_ids=["EVT-JIRA-001"],
            expected_risk_types=[RiskType.BLOCKER],
            expected_severities=[RiskSeverity.HIGH],
            expected_evidence_event_ids=["EVT-JIRA-001"],
        ),
        RiskEvaluationCase(
            case_id="RISK-007",
            project_id="PROJ-001",
            evidence_event_ids=["EVT-JIRA-001"],
            expected_risk_types=[RiskType.BLOCKER],
            expected_severities=[RiskSeverity.HIGH],
            expected_evidence_event_ids=["EVT-JIRA-001"],
        ),
    ]

    evaluation_run = evaluator.evaluate(
        cases=cases,
        evidence_by_case={
            "RISK-006": _evidence(),
            "RISK-007": _evidence(),
        },
    )

    summary = evaluation_run.summary

    assert summary.total_cases == 2
    assert summary.true_positive_count == 1
    assert summary.false_positive_count == 1
    assert summary.false_negative_count == 1
    assert summary.precision == 0.5
    assert summary.recall == 0.5
    assert summary.f1 == 0.5
    assert summary.severity_accuracy == 1.0
    assert summary.evidence_accuracy == 1.0

    assert len(evaluation_run.results) == 2


def test_evaluate_empty_cases_returns_zero_metrics() -> None:
    analyzer = Mock()

    evaluator = RiskEvaluator(analyze=analyzer)

    evaluation_run = evaluator.evaluate(
        cases=[],
        evidence_by_case={},
    )

    summary = evaluation_run.summary

    assert evaluation_run.results == []
    assert summary.total_cases == 0
    assert summary.true_positive_count == 0
    assert summary.false_positive_count == 0
    assert summary.false_negative_count == 0
    assert summary.precision == 0.0
    assert summary.recall == 0.0
    assert summary.f1 == 0.0
    assert summary.severity_accuracy == 0.0
    assert summary.evidence_accuracy == 0.0