from abc import ABC, abstractmethod

from ai_project_health_monitor.domain.models.health_alert import HealthAlert


class AlertDelivery(ABC):
    """Contract for delivering project health alerts to an external channel."""

    @abstractmethod
    def deliver(self, alert: HealthAlert) -> None:
        """Deliver a project health alert."""
        raise NotImplementedError