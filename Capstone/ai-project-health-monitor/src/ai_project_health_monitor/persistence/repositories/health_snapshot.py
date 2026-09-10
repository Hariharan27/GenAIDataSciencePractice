from abc import ABC, abstractmethod

from ai_project_health_monitor.persistence.health_snapshot import (
    ProjectHealthSnapshot,
)


class HealthSnapshotRepository(ABC):
    """Repository contract for project health snapshots."""

    @abstractmethod
    def save(self, snapshot: ProjectHealthSnapshot) -> None:
        """Persist a project health snapshot."""
        raise NotImplementedError

    @abstractmethod
    def get_latest(self, project_id: str) -> ProjectHealthSnapshot | None:
        """Return the latest snapshot for a project."""
        raise NotImplementedError

    @abstractmethod
    def get_history(
        self,
        project_id: str,
    ) -> list[ProjectHealthSnapshot]:
        """Return project health snapshots in chronological order."""
        raise NotImplementedError