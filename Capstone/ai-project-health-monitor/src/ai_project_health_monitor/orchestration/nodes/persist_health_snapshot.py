from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.persistence.health_snapshot import (
    ProjectHealthSnapshot,
)
from ai_project_health_monitor.persistence.repositories.health_snapshot import (
    HealthSnapshotRepository,
)


class PersistHealthSnapshotNode:
    """LangGraph node responsible for persisting project health."""

    def __init__(
        self,
        health_snapshot_repository: HealthSnapshotRepository,
    ) -> None:
        self._health_snapshot_repository = health_snapshot_repository

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        if state.health_score is None:
            raise ValueError(
                "health_score must be available before persisting a snapshot"
            )

        snapshot = ProjectHealthSnapshot(
            project_id=state.project_id,
            health_score=state.health_score.score,
            health_status=state.health_score.status,
            risk_signals=state.primary_risks,
            calculated_at=state.health_score.calculated_at,
        )

        self._health_snapshot_repository.save(snapshot)

        return {}