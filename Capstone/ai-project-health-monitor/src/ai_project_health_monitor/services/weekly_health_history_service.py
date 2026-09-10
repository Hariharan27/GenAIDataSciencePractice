from datetime import datetime

from ai_project_health_monitor.domain.models.weekly_health_history import (
    HealthHistoryPoint,
    WeeklyHealthHistory,
)
from ai_project_health_monitor.persistence.repositories.health_snapshot import (
    HealthSnapshotRepository,
)


class WeeklyHealthHistoryService:
    """Builds weekly health history from persisted project snapshots."""

    def __init__(
        self,
        health_snapshot_repository: HealthSnapshotRepository,
    ) -> None:
        self._health_snapshot_repository = health_snapshot_repository

    def get_history(
        self,
        project_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> WeeklyHealthHistory:
        if not project_id.strip():
            raise ValueError("project_id cannot be empty")

        if start_date > end_date:
            raise ValueError("start_date cannot be after end_date")

        snapshots = self._health_snapshot_repository.get_history(project_id)

        history_points = [
            HealthHistoryPoint(
                calculated_at=snapshot.calculated_at,
                health_score=snapshot.health_score,
                health_status=snapshot.health_status,
                risk_signals=snapshot.risk_signals,
            )
            for snapshot in snapshots
            if start_date <= snapshot.calculated_at <= end_date
        ]

        return WeeklyHealthHistory(
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            snapshots=history_points,
        )