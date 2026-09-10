from datetime import datetime

import pytest

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.weekly_health_analysis import (
    WeeklyHealthAnalysis,
)
from ai_project_health_monitor.domain.models.weekly_health_history import (
    HealthHistoryPoint,
    WeeklyHealthHistory,
)
from ai_project_health_monitor.services.weekly_health_analysis_service import (
    WeeklyHealthAnalysisService,
)


def test_analyze_derives_health_deterioration() -> None:
    history = WeeklyHealthHistory(
        project_id="PROJ-001",
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 7),
        snapshots=[
            HealthHistoryPoint(
                calculated_at=datetime(2026, 9, 1),
                health_score=82.0,
                health_status=HealthStatus.HEALTHY,
            ),
            HealthHistoryPoint(
                calculated_at=datetime(2026, 9, 3),
                health_score=74.0,
                health_status=HealthStatus.HEALTHY,
            ),
            HealthHistoryPoint(
                calculated_at=datetime(2026, 9, 7),
                health_score=61.0,
                health_status=HealthStatus.AT_RISK,
            ),
        ],
    )

    analysis = WeeklyHealthAnalysisService().analyze(history)

    assert analysis == WeeklyHealthAnalysis(
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


def test_analyze_derives_health_improvement() -> None:
    history = WeeklyHealthHistory(
        project_id="PROJ-001",
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 7),
        snapshots=[
            HealthHistoryPoint(
                calculated_at=datetime(2026, 9, 1),
                health_score=55.0,
                health_status=HealthStatus.AT_RISK,
            ),
            HealthHistoryPoint(
                calculated_at=datetime(2026, 9, 5),
                health_score=78.0,
                health_status=HealthStatus.HEALTHY,
            ),
        ],
    )

    analysis = WeeklyHealthAnalysisService().analyze(history)

    assert analysis.score_change == 23.0
    assert analysis.health_improved is True
    assert analysis.health_deteriorated is False


def test_analyze_sorts_snapshots_before_calculating_change() -> None:
    history = WeeklyHealthHistory(
        project_id="PROJ-001",
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 7),
        snapshots=[
            HealthHistoryPoint(
                calculated_at=datetime(2026, 9, 7),
                health_score=60.0,
                health_status=HealthStatus.AT_RISK,
            ),
            HealthHistoryPoint(
                calculated_at=datetime(2026, 9, 1),
                health_score=80.0,
                health_status=HealthStatus.HEALTHY,
            ),
        ],
    )

    analysis = WeeklyHealthAnalysisService().analyze(history)

    assert analysis.starting_score == 80.0
    assert analysis.ending_score == 60.0
    assert analysis.score_change == -20.0


def test_analyze_rejects_empty_history() -> None:
    history = WeeklyHealthHistory(
        project_id="PROJ-001",
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 7),
    )

    with pytest.raises(
        ValueError,
        match="weekly health history contains no snapshots",
    ):
        WeeklyHealthAnalysisService().analyze(history)