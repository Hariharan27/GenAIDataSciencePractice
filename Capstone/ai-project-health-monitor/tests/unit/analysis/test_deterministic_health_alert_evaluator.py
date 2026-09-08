from datetime import UTC, datetime

import pytest

from ai_project_health_monitor.analysis.deterministic_health_alert_evaluator import (
    DeterministicHealthAlertEvaluator,
)
from ai_project_health_monitor.domain.models.health_score import (
    HealthScore,
    HealthStatus,
)


@pytest.fixture
def evaluator() -> DeterministicHealthAlertEvaluator:
    return DeterministicHealthAlertEvaluator()


def test_evaluate_triggers_alert_for_critical_project(
    evaluator: DeterministicHealthAlertEvaluator,
) -> None:
    health_score = HealthScore(
        project_id="PROJ-001",
        score=35.0,
        status=HealthStatus.CRITICAL,
        contributing_risks=["SIG-001"],
        calculated_at=datetime(2026, 9, 1, tzinfo=UTC),
        rationale="Critical delivery risk.",
    )

    result = evaluator.evaluate(health_score)

    assert result.project_id == "PROJ-001"
    assert result.health_score == 35.0
    assert result.health_status == HealthStatus.CRITICAL
    assert result.triggered is True
    assert "Immediate attention is required." in result.message


@pytest.mark.parametrize(
    ("status", "score"),
    [
        (HealthStatus.HEALTHY, 85.0),
        (HealthStatus.AT_RISK, 60.0),
    ],
)
def test_evaluate_does_not_trigger_alert_for_non_critical_project(
    evaluator: DeterministicHealthAlertEvaluator,
    status: HealthStatus,
    score: float,
) -> None:
    health_score = HealthScore(
        project_id="PROJ-001",
        score=score,
        status=status,
        contributing_risks=[],
        calculated_at=datetime(2026, 9, 1, tzinfo=UTC),
        rationale="Project health is stable.",
    )

    result = evaluator.evaluate(health_score)

    assert result.triggered is False
    assert result.health_status == status
    assert result.health_score == score
    assert "does not require a critical alert" in result.message


def test_evaluate_preserves_project_health_facts(
    evaluator: DeterministicHealthAlertEvaluator,
) -> None:
    health_score = HealthScore(
        project_id="PROJ-002",
        score=25.5,
        status=HealthStatus.CRITICAL,
        contributing_risks=["SIG-001", "SIG-002"],
        calculated_at=datetime(2026, 9, 1, tzinfo=UTC),
        rationale="Multiple critical risks detected.",
    )

    result = evaluator.evaluate(health_score)

    assert result.project_id == health_score.project_id
    assert result.health_score == health_score.score
    assert result.health_status == health_score.status