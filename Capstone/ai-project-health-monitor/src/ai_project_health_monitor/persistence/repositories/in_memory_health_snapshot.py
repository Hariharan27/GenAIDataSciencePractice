from ai_project_health_monitor.persistence.health_snapshot import (
    ProjectHealthSnapshot,
)
from ai_project_health_monitor.persistence.repositories.health_snapshot import (
    HealthSnapshotRepository,
)


class InMemoryHealthSnapshotRepository(HealthSnapshotRepository):
    """In-memory repository for project health snapshots."""

    def __init__(self) -> None:
        self._snapshots: dict[str, list[ProjectHealthSnapshot]] = {}

    def save(self, snapshot: ProjectHealthSnapshot) -> None:
        """Store a project health snapshot."""
        self._snapshots.setdefault(snapshot.project_id, []).append(snapshot)

    def get_latest(self, project_id: str) -> ProjectHealthSnapshot | None:
        """Return the latest snapshot for a project."""
        snapshots = self._snapshots.get(project_id, [])
        if not snapshots:
            return None

        return max(snapshots, key=lambda snapshot: snapshot.calculated_at)

    def get_history(
        self,
        project_id: str,
    ) -> list[ProjectHealthSnapshot]:
        """Return project health snapshots in chronological order."""
        snapshots = self._snapshots.get(project_id, [])
        return sorted(
            snapshots,
            key=lambda snapshot: snapshot.calculated_at,
        )