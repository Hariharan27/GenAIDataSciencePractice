from abc import ABC, abstractmethod

from ai_project_health_monitor.domain.models.health_alert import HealthAlert


class AlertNotifier(ABC):
    """Contract for delivering project health alerts to stakeholders."""

    @abstractmethod
    def notify(self, alert: HealthAlert) -> None:
        """Deliver a health alert to the configured stakeholder channel."""
        raise NotImplementedError