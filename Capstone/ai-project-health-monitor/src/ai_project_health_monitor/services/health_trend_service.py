from ai_project_health_monitor.domain.models.health_trend import HealthTrend
from ai_project_health_monitor.persistence.repositories.health_snapshot import (
    HealthSnapshotRepository,
)


class HealthTrendService:
    """Derives project health trends from historical snapshots."""

    def __init__(self, health_snapshot_repository: HealthSnapshotRepository) -> None:
        self._health_snapshot_repository = health_snapshot_repository

    def get_trend(self, project_id: str) -> HealthTrend | None:
        """Return the current health trend for a project."""
        if not project_id.strip():
            raise ValueError("project_id cannot be empty")

        snapshots = self._health_snapshot_repository.get_history(project_id)

        if not snapshots:
            return None

        current = snapshots[-1]

        if len(snapshots) == 1:
            return HealthTrend(
                project_id=project_id,
                current_score=current.health_score,
                current_status=current.health_status,
            )

        previous = snapshots[-2]

        return HealthTrend(
            project_id=project_id,
            current_score=current.health_score,
            previous_score=previous.health_score,
            current_status=current.health_status,
            score_change=current.health_score - previous.health_score,
        )