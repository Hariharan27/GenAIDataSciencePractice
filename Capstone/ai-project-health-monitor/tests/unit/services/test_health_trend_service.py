from datetime import datetime, timedelta

import pytest

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.persistence.health_snapshot import ProjectHealthSnapshot
from ai_project_health_monitor.persistence.repositories.in_memory_health_snapshot import (
    InMemoryHealthSnapshotRepository,
)
from ai_project_health_monitor.services.health_trend_service import HealthTrendService


def test_get_trend_returns_current_and_previous_scores() -> None:
    repository = InMemoryHealthSnapshotRepository()
    calculated_at = datetime(2026, 9, 10, 10, 0, 0)

    repository.save(
        ProjectHealthSnapshot(
            project_id="PROJ-001",
            health_score=80.0,
            health_status=HealthStatus.HEALTHY,
            calculated_at=calculated_at,
        )
    )
    repository.save(
        ProjectHealthSnapshot(
            project_id="PROJ-001",
            health_score=65.0,
            health_status=HealthStatus.AT_RISK,
            calculated_at=calculated_at + timedelta(hours=1),
        )
    )

    service = HealthTrendService(repository)

    trend = service.get_trend("PROJ-001")

    assert trend is not None
    assert trend.current_score == 65.0
    assert trend.previous_score == 80.0
    assert trend.current_status == HealthStatus.AT_RISK
    assert trend.score_change == -15.0


def test_get_trend_returns_no_change_when_only_one_snapshot_exists() -> None:
    repository = InMemoryHealthSnapshotRepository()

    repository.save(
        ProjectHealthSnapshot(
            project_id="PROJ-001",
            health_score=75.0,
            health_status=HealthStatus.AT_RISK,
            calculated_at=datetime(2026, 9, 10, 10, 0, 0),
        )
    )

    service = HealthTrendService(repository)

    trend = service.get_trend("PROJ-001")

    assert trend is not None
    assert trend.current_score == 75.0
    assert trend.previous_score is None
    assert trend.score_change is None


def test_get_trend_returns_none_when_project_has_no_snapshots() -> None:
    repository = InMemoryHealthSnapshotRepository()
    service = HealthTrendService(repository)

    trend = service.get_trend("PROJ-001")

    assert trend is None


def test_get_trend_rejects_empty_project_id() -> None:
    repository = InMemoryHealthSnapshotRepository()
    service = HealthTrendService(repository)

    with pytest.raises(ValueError, match="project_id cannot be empty"):
        service.get_trend("   ")