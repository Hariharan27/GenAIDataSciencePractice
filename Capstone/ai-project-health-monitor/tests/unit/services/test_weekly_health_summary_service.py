from datetime import datetime
from unittest.mock import Mock

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.weekly_health_analysis import (
    WeeklyHealthAnalysis,
)
from ai_project_health_monitor.domain.models.weekly_health_history import (
    WeeklyHealthHistory,
)
from ai_project_health_monitor.domain.models.weekly_health_summary import (
    WeeklyHealthSummary,
)
from ai_project_health_monitor.services.weekly_health_summary_service import (
    WeeklyHealthSummaryService,
)


def test_generate_coordinates_weekly_summary_pipeline() -> None:
    history_service = Mock()
    analysis_service = Mock()
    summary_generator = Mock()
    risk_evolution_service = Mock()

    history = WeeklyHealthHistory(
        project_id="PROJ-001",
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 7),
    )

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

    expected_summary = WeeklyHealthSummary(
        project_id="PROJ-001",
        starting_score=82.0,
        ending_score=61.0,
        score_change=-21.0,
        starting_status=HealthStatus.HEALTHY,
        ending_status=HealthStatus.AT_RISK,
        health_improved=False,
        health_deteriorated=True,
        summary="Project health deteriorated during the week.",
        outlook="Release risk remains elevated.",
        recommended_actions=[
            "Resolve the payment integration blocker.",
        ],
    )

    history_service.get_history.return_value = history
    analysis_service.analyze.return_value = analysis
    summary_generator.generate.return_value = expected_summary
    risk_evolution_service.analyze.return_value = []

    service = WeeklyHealthSummaryService(
        weekly_health_history_service=history_service,
        weekly_health_analysis_service=analysis_service,
        weekly_health_summary_generator=summary_generator,
        weekly_risk_evolution_service=risk_evolution_service,
    )

    result = service.generate(
        project_id="PROJ-001",
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 7),
        key_risks=[],
    )

    assert result == expected_summary

    history_service.get_history.assert_called_once_with(
        project_id="PROJ-001",
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 7),
    )

    analysis_service.analyze.assert_called_once_with(history)
    risk_evolution_service.analyze.assert_called_once_with(history)

    summary_generator.generate.assert_called_once_with(
        analysis=analysis,
        key_risks=[],
        risk_evolution=risk_evolution_service.analyze.return_value,
    )