from datetime import datetime

from psycopg.types.json import Jsonb
import psycopg
from psycopg.rows import dict_row

from ai_project_health_monitor.persistence.health_snapshot import (
    ProjectHealthSnapshot,
)
from ai_project_health_monitor.persistence.repositories.health_snapshot import (
    HealthSnapshotRepository,
)


class PostgresHealthSnapshotRepository(HealthSnapshotRepository):
    """PostgreSQL repository for project health snapshots."""

    def __init__(self, dsn: str) -> None:
        if not dsn.strip():
            raise ValueError("dsn cannot be empty")
        self._dsn = dsn

    def save(self, snapshot: ProjectHealthSnapshot) -> None:
        """Persist a project health snapshot."""
        with psycopg.connect(self._dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO project_health_snapshots (
                        project_id,
                        health_score,
                        health_status,
                        risk_signals,
                        calculated_at,
                        evidence_fingerprint
                    )
                    VALUES (
                        %(project_id)s,
                        %(health_score)s,
                        %(health_status)s,
                        %(risk_signals)s::jsonb,
                        %(calculated_at)s,
                        %(evidence_fingerprint)s
                    )
                    """,
                    {
                        "project_id": snapshot.project_id,
                        "health_score": snapshot.health_score,
                        "health_status": snapshot.health_status.value,
                        "risk_signals": Jsonb(
                            snapshot.model_dump(
                                mode="json",
                                include={"risk_signals"},
                            )["risk_signals"],
                        ),
                        "calculated_at": snapshot.calculated_at,
                        "evidence_fingerprint": snapshot.evidence_fingerprint,
                    },
                )
            connection.commit()

    def get_latest(
        self,
        project_id: str,
    ) -> ProjectHealthSnapshot | None:
        """Return the latest snapshot for a project."""
        with psycopg.connect(
            self._dsn,
            row_factory=dict_row,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        project_id,
                        health_score,
                        health_status,
                        risk_signals,
                        calculated_at,
                        evidence_fingerprint
                    FROM project_health_snapshots
                    WHERE project_id = %s
                    ORDER BY calculated_at DESC
                    LIMIT 1
                    """,
                    (project_id,),
                )
                row = cursor.fetchone()

        if row is None:
            return None

        return self._to_snapshot(row)

    def get_history(
        self,
        project_id: str,
    ) -> list[ProjectHealthSnapshot]:
        """Return project health snapshots in chronological order."""
        with psycopg.connect(
            self._dsn,
            row_factory=dict_row,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        project_id,
                        health_score,
                        health_status,
                        risk_signals,
                        calculated_at,
                        evidence_fingerprint
                    FROM project_health_snapshots
                    WHERE project_id = %s
                    ORDER BY calculated_at ASC
                    """,
                    (project_id,),
                )
                rows = cursor.fetchall()

        return [self._to_snapshot(row) for row in rows]

    @staticmethod
    def _to_snapshot(row: dict) -> ProjectHealthSnapshot:
        """Convert a database row into a health snapshot."""
        return ProjectHealthSnapshot(
            project_id=row["project_id"],
            health_score=row["health_score"],
            health_status=row["health_status"],
            risk_signals=row["risk_signals"],
            calculated_at=_as_datetime(row["calculated_at"]),
            evidence_fingerprint=row["evidence_fingerprint"],
        )


def _as_datetime(value: datetime) -> datetime:
    """Return a database datetime as a timezone-aware datetime."""
    return value