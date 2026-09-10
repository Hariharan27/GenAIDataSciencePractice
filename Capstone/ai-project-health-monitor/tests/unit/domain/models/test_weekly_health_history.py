from datetime import datetime

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.weekly_health_history import (
    HealthHistoryPoint,
    WeeklyHealthHistory,
)


def test_weekly_health_history_contains_snapshots() -> None:
    start_date = datetime(2026, 9, 1)
    end_date = datetime(2026, 9, 7)

    history = WeeklyHealthHistory(
        project_id="PROJ-001",
        start_date=start_date,
        end_date=end_date,
        snapshots=[
            HealthHistoryPoint(
                calculated_at=datetime(2026, 9, 3),
                health_score=80.0,
                health_status=HealthStatus.HEALTHY,
            ),
            HealthHistoryPoint(
                calculated_at=datetime(2026, 9, 7),
                health_score=65.0,
                health_status=HealthStatus.AT_RISK,
            ),
        ],
    )

    assert history.project_id == "PROJ-001"
    assert history.start_date == start_date
    assert history.end_date == end_date
    assert len(history.snapshots) == 2
    assert history.snapshots[0].health_score == 80.0
    assert history.snapshots[1].health_status == HealthStatus.AT_RISK


def test_weekly_health_history_defaults_to_empty_snapshots() -> None:
    history = WeeklyHealthHistory(
        project_id="PROJ-001",
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 7),
    )

    assert history.snapshots == []