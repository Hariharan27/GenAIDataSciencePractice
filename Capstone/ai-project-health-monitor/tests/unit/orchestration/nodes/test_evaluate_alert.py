from datetime import UTC, datetime
from unittest.mock import Mock

from ai_project_health_monitor.analysis.health_alert_evaluator import (
    HealthAlertEvaluator,
)
from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.domain.models.health_score import (
    HealthScore,
    HealthStatus,
)
from ai_project_health_monitor.orchestration.nodes.evaluate_alert import (
    EvaluateAlertNode,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState


def test_evaluate_alert_node_generates_alert() -> None:
    evaluator = Mock(spec=HealthAlertEvaluator)
    node = EvaluateAlertNode(alert_evaluator=evaluator)

    health_score = HealthScore(
        project_id="PROJ-001",
        score=35.0,
        status=HealthStatus.CRITICAL,
        contributing_risks=["SIG-001"],
        calculated_at=datetime(2026, 9, 1, tzinfo=UTC),
        rationale="Critical delivery risk.",
    )

    alert = HealthAlert(
        project_id="PROJ-001",
        health_score=35.0,
        health_status=HealthStatus.CRITICAL,
        message="Immediate attention is required.",
        triggered=True,
    )

    evaluator.evaluate.return_value = alert

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What is the current project health?",
        health_score=health_score,
    )

    result = node(state)

    assert result == {"alert": alert}

    evaluator.evaluate.assert_called_once_with(
        health_score=health_score,
    )


def test_evaluate_alert_node_requires_health_score() -> None:
    evaluator = Mock(spec=HealthAlertEvaluator)
    node = EvaluateAlertNode(alert_evaluator=evaluator)

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What is the current project health?",
    )

    try:
        node(state)
    except ValueError as exc:
        assert str(exc) == "health_score must be available before evaluating alert"
    else:
        raise AssertionError("Expected ValueError")