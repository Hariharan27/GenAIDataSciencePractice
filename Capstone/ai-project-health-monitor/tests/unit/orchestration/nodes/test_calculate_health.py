from datetime import UTC, datetime
from unittest.mock import Mock

from ai_project_health_monitor.analysis.health_scorer import HealthScorer
from ai_project_health_monitor.domain.models.health_score import (
    HealthScore,
    HealthStatus,
)
from ai_project_health_monitor.domain.models.risk_signal import RiskSignal
from ai_project_health_monitor.orchestration.nodes.calculate_health import (
    CalculateHealthNode,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState


def test_calculate_health_node_calculates_health_from_primary_risks() -> None:
    health_scorer = Mock(spec=HealthScorer)

    risk_signal = Mock(spec=RiskSignal)

    expected_health_score = HealthScore(
        project_id="PROJ-001",
        score=60.0,
        status=HealthStatus.AT_RISK,
        contributing_risks=["SIG-001"],
        calculated_at=datetime(
            2026,
            9,
            1,
            tzinfo=UTC,
        ),
        rationale="Project has significant delivery risks.",
    )

    health_scorer.calculate.return_value = expected_health_score

    node = CalculateHealthNode(
        health_scorer=health_scorer,
    )

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What risks are affecting the project?",
        primary_risks=[risk_signal],
    )

    result = node(state)

    assert result["health_score"] == expected_health_score

    health_scorer.calculate.assert_called_once_with(
        project_id="PROJ-001",
        risk_signals=[risk_signal],
    )