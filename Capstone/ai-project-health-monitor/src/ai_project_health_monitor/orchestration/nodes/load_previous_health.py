from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.persistence.repositories.health_snapshot import (
    HealthSnapshotRepository,
)


class LoadPreviousHealthNode:
    """LangGraph node responsible for loading the latest project health snapshot."""

    def __init__(
        self,
        health_snapshot_repository: HealthSnapshotRepository,
    ) -> None:
        self._health_snapshot_repository = health_snapshot_repository

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        previous_snapshot = self._health_snapshot_repository.get_latest(
            state.project_id,
        )

        return {
            "previous_health_snapshot": previous_snapshot,
        }