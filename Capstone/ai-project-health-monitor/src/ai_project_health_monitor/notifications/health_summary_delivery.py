from abc import ABC, abstractmethod

from ai_project_health_monitor.domain.models.project_health_summary import (
    ProjectHealthSummary,
)


class HealthSummaryDelivery(ABC):
    """Contract for delivering project health summaries to stakeholders."""

    @abstractmethod
    def deliver(self, summary: ProjectHealthSummary) -> None:
        """Deliver a project health summary."""
        raise NotImplementedError