from abc import ABC, abstractmethod

from ai_project_health_monitor.domain.models.project_health_summary import (
    ProjectHealthSummary,
)


class HealthSummaryNotifier(ABC):
    """Contract for notifying stakeholders about project health summaries."""

    @abstractmethod
    def notify(self, summary: ProjectHealthSummary) -> None:
        """Notify stakeholders about a project health summary."""
        raise NotImplementedError