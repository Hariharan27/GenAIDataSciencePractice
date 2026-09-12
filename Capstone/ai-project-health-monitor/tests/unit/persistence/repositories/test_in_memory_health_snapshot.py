from datetime import UTC, datetime

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.persistence.health_snapshot import (
    ProjectHealthSnapshot,
)
from ai_project_health_monitor.persistence.repositories.in_memory_health_snapshot import (
    InMemoryHealthSnapshotRepository,
)


def create_snapshot(
    project_id: str,
    score: float,
    calculated_at: datetime,
) -> ProjectHealthSnapshot:
    return ProjectHealthSnapshot(
        project_id=project_id,
        health_score=score,
        health_status=HealthStatus.HEALTHY,
        evidence_fingerprint="dummy_fingerprint",
        calculated_at=calculated_at,
    )


def test_save_and_get_latest() -> None:
    repository = InMemoryHealthSnapshotRepository()

    first = create_snapshot(
        project_id="PROJ-001",
        score=80.0,
        calculated_at=datetime(2026, 9, 10, 10, tzinfo=UTC),
    )
    latest = create_snapshot(
        project_id="PROJ-001",
        score=60.0,
        calculated_at=datetime(2026, 9, 10, 11, tzinfo=UTC),
    )

    repository.save(first)
    repository.save(latest)

    assert repository.get_latest("PROJ-001") == latest


def test_get_latest_returns_none_when_project_has_no_snapshots() -> None:
    repository = InMemoryHealthSnapshotRepository()

    assert repository.get_latest("PROJ-001") is None


def test_get_history_returns_snapshots_in_chronological_order() -> None:
    repository = InMemoryHealthSnapshotRepository()

    latest = create_snapshot(
        project_id="PROJ-001",
        score=60.0,
        calculated_at=datetime(2026, 9, 10, 11, tzinfo=UTC),
    )
    first = create_snapshot(
        project_id="PROJ-001",
        score=80.0,
        calculated_at=datetime(2026, 9, 10, 10, tzinfo=UTC),
    )

    repository.save(latest)
    repository.save(first)

    assert repository.get_history("PROJ-001") == [first, latest]


def test_project_snapshots_are_isolated() -> None:
    repository = InMemoryHealthSnapshotRepository()

    snapshot = create_snapshot(
        project_id="PROJ-001",
        score=80.0,
        calculated_at=datetime(2026, 9, 10, 10, tzinfo=UTC),
    )

    repository.save(snapshot)

    assert repository.get_latest("PROJ-002") is None
    assert repository.get_history("PROJ-002") == []