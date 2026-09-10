from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.health_trend import HealthTrend


def test_health_trend_with_previous_score() -> None:
    trend = HealthTrend(
        project_id="PROJ-001",
        current_score=70.0,
        previous_score=80.0,
        current_status=HealthStatus.AT_RISK,
        score_change=-10.0,
    )

    assert trend.project_id == "PROJ-001"
    assert trend.current_score == 70.0
    assert trend.previous_score == 80.0
    assert trend.current_status == HealthStatus.AT_RISK
    assert trend.score_change == -10.0


def test_health_trend_without_previous_score() -> None:
    trend = HealthTrend(
        project_id="PROJ-001",
        current_score=85.0,
        current_status=HealthStatus.HEALTHY,
    )

    assert trend.project_id == "PROJ-001"
    assert trend.current_score == 85.0
    assert trend.previous_score is None
    assert trend.current_status == HealthStatus.HEALTHY
    assert trend.score_change is None