from datetime import UTC, datetime

import psycopg

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.persistence.health_snapshot import (
    ProjectHealthSnapshot,
)
from ai_project_health_monitor.persistence.repositories.postgres_health_snapshot import (
    PostgresHealthSnapshotRepository,
)


POSTGRES_DSN = (
    "postgresql://postgres:postgres@localhost:5434/"
    "ai_project_health_monitor"
)

def _clear_test_project() -> None:
    with psycopg.connect(POSTGRES_DSN) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM project_health_snapshots
                WHERE project_id = %s
                """,
                ("TEST-PROJ",),
            )
        connection.commit()


def _snapshot(
    project_id: str,
    score: float,
    calculated_at: datetime,
    fingerprint: str,
) -> ProjectHealthSnapshot:
    return ProjectHealthSnapshot(
        project_id=project_id,
        health_score=score,
        health_status=HealthStatus.HEALTHY,
        risk_signals=[],
        calculated_at=calculated_at,
        evidence_fingerprint=fingerprint,
    )


def test_postgres_repository_saves_and_reads_snapshots() -> None:
    repository = PostgresHealthSnapshotRepository(POSTGRES_DSN)
    _clear_test_project()

    first = _snapshot(
        project_id="TEST-PROJ",
        score=80.0,
        calculated_at=datetime(2026, 9, 12, 10, tzinfo=UTC),
        fingerprint="fingerprint-1",
    )
    second = _snapshot(
        project_id="TEST-PROJ",
        score=65.0,
        calculated_at=datetime(2026, 9, 12, 11, tzinfo=UTC),
        fingerprint="fingerprint-2",
    )

    repository.save(first)
    repository.save(second)

    latest = repository.get_latest("TEST-PROJ")
    history = repository.get_history("TEST-PROJ")

    assert latest.project_id == second.project_id
    assert latest.health_score == second.health_score
    assert latest.health_status == second.health_status
    assert latest.risk_signals == second.risk_signals
    assert latest.evidence_fingerprint == second.evidence_fingerprint
    assert latest.calculated_at == second.calculated_at.astimezone(UTC)

    assert len(history) == 2
    assert history[0].project_id == first.project_id
    assert history[0].health_score == first.health_score
    assert history[0].health_status == first.health_status
    assert history[0].risk_signals == first.risk_signals
    assert history[0].evidence_fingerprint == first.evidence_fingerprint
    assert history[0].calculated_at == first.calculated_at.astimezone(UTC)

    assert history[1].project_id == second.project_id
    assert history[1].health_score == second.health_score
    assert history[1].health_status == second.health_status
    assert history[1].risk_signals == second.risk_signals
    assert history[1].evidence_fingerprint == second.evidence_fingerprint
    assert history[1].calculated_at == second.calculated_at.astimezone(UTC)