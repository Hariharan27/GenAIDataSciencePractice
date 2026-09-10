from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.weekly_health_analysis import (
    WeeklyHealthAnalysis,
)


def test_weekly_health_analysis_represents_health_deterioration() -> None:
    analysis = WeeklyHealthAnalysis(
        project_id="PROJ-001",
        starting_score=82.0,
        ending_score=61.0,
        score_change=-21.0,
        highest_score=82.0,
        lowest_score=61.0,
        starting_status=HealthStatus.HEALTHY,
        ending_status=HealthStatus.AT_RISK,
        observation_count=4,
        health_improved=False,
        health_deteriorated=True,
    )

    assert analysis.project_id == "PROJ-001"
    assert analysis.starting_score == 82.0
    assert analysis.ending_score == 61.0
    assert analysis.score_change == -21.0
    assert analysis.highest_score == 82.0
    assert analysis.lowest_score == 61.0
    assert analysis.starting_status == HealthStatus.HEALTHY
    assert analysis.ending_status == HealthStatus.AT_RISK
    assert analysis.observation_count == 4
    assert analysis.health_improved is False
    assert analysis.health_deteriorated is True


def test_weekly_health_analysis_represents_health_improvement() -> None:
    analysis = WeeklyHealthAnalysis(
        project_id="PROJ-001",
        starting_score=55.0,
        ending_score=78.0,
        score_change=23.0,
        highest_score=78.0,
        lowest_score=55.0,
        starting_status=HealthStatus.AT_RISK,
        ending_status=HealthStatus.HEALTHY,
        observation_count=3,
        health_improved=True,
        health_deteriorated=False,
    )

    assert analysis.score_change == 23.0
    assert analysis.health_improved is True
    assert analysis.health_deteriorated is False