from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.weekly_health_analysis import (
    WeeklyHealthAnalysis,
)
from ai_project_health_monitor.domain.models.weekly_health_summary import (
    WeeklyHealthSummary,
)
from ai_project_health_monitor.services.weekly_health_summary_generator import (
    WeeklyHealthSummaryGenerator,
)


class FakeWeeklyHealthSummaryGenerator(WeeklyHealthSummaryGenerator):
    """Test implementation of the summary generator contract."""

    def generate(
        self,
        analysis: WeeklyHealthAnalysis,
        key_risks: list,
        risk_evolution: list,
    ) -> WeeklyHealthSummary:
        return WeeklyHealthSummary(
            project_id=analysis.project_id,
            starting_score=analysis.starting_score,
            ending_score=analysis.ending_score,
            score_change=analysis.score_change,
            starting_status=analysis.starting_status,
            ending_status=analysis.ending_status,
            health_improved=analysis.health_improved,
            health_deteriorated=analysis.health_deteriorated,
            key_risks=key_risks,
            summary="Test weekly summary.",
            outlook="Test outlook.",
            recommended_actions=["Test action."],
        )


def test_weekly_health_summary_generator_contract() -> None:
    analysis = WeeklyHealthAnalysis(
        project_id="PROJ-001",
        starting_score=82.0,
        ending_score=61.0,
        score_change=-21.0,
        highest_score=82.0,
        lowest_score=61.0,
        starting_status=HealthStatus.HEALTHY,
        ending_status=HealthStatus.AT_RISK,
        observation_count=3,
        health_improved=False,
        health_deteriorated=True,
    )

    generator = FakeWeeklyHealthSummaryGenerator()

    summary = generator.generate(
        analysis=analysis,
        key_risks=[],
        risk_evolution=[],
    )

    assert summary.project_id == "PROJ-001"
    assert summary.starting_score == 82.0
    assert summary.ending_score == 61.0
    assert summary.score_change == -21.0
    assert summary.health_deteriorated is True
    assert summary.summary == "Test weekly summary."
    assert summary.outlook == "Test outlook."
    assert summary.recommended_actions == ["Test action."]