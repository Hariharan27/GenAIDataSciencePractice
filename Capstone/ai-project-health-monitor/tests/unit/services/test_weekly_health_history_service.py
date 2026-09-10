from datetime import datetime

import pytest

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.persistence.health_snapshot import ProjectHealthSnapshot
from ai_project_health_monitor.persistence.repositories.in_memory_health_snapshot import (
    InMemoryHealthSnapshotRepository,
)
from ai_project_health_monitor.services.weekly_health_history_service import (
    WeeklyHealthHistoryService,
)


def test_get_history_returns_snapshots_within_date_range() -> None:
    repository = InMemoryHealthSnapshotRepository()

    repository.save(
        ProjectHealthSnapshot(
            project_id="PROJ-001",
            health_score=80.0,
            health_status=HealthStatus.HEALTHY,
            calculated_at=datetime(2026, 9, 1),
        )
    )
    repository.save(
        ProjectHealthSnapshot(
            project_id="PROJ-001",
            health_score=70.0,
            health_status=HealthStatus.AT_RISK,
            calculated_at=datetime(2026, 9, 4),
        )
    )
    repository.save(
        ProjectHealthSnapshot(
            project_id="PROJ-001",
            health_score=50.0,
            health_status=HealthStatus.CRITICAL,
            calculated_at=datetime(2026, 9, 10),
        )
    )

    service = WeeklyHealthHistoryService(repository)

    history = service.get_history(
        project_id="PROJ-001",
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 7),
    )

    assert len(history.snapshots) == 2
    assert history.snapshots[0].health_score == 80.0
    assert history.snapshots[1].health_score == 70.0


def test_get_history_returns_empty_history_when_no_snapshots_match() -> None:
    repository = InMemoryHealthSnapshotRepository()

    repository.save(
        ProjectHealthSnapshot(
            project_id="PROJ-001",
            health_score=80.0,
            health_status=HealthStatus.HEALTHY,
            calculated_at=datetime(2026, 9, 10),
        )
    )

    service = WeeklyHealthHistoryService(repository)

    history = service.get_history(
        project_id="PROJ-001",
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 7),
    )

    assert history.snapshots == []


def test_get_history_rejects_empty_project_id() -> None:
    repository = InMemoryHealthSnapshotRepository()
    service = WeeklyHealthHistoryService(repository)

    with pytest.raises(ValueError, match="project_id cannot be empty"):
        service.get_history(
            project_id=" ",
            start_date=datetime(2026, 9, 1),
            end_date=datetime(2026, 9, 7),
        )


def test_get_history_rejects_invalid_date_range() -> None:
    repository = InMemoryHealthSnapshotRepository()
    service = WeeklyHealthHistoryService(repository)

    with pytest.raises(ValueError, match="start_date cannot be after end_date"):
        service.get_history(
            project_id="PROJ-001",
            start_date=datetime(2026, 9, 7),
            end_date=datetime(2026, 9, 1),
        )