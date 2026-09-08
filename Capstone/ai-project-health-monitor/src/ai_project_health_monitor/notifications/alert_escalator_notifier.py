from abc import ABC, abstractmethod

from ai_project_health_monitor.domain.models.health_alert import HealthAlert


class AlertEscalatorNotifier(ABC):
    """Contract for delivering escalated project health alerts."""

    @abstractmethod
    def notify_escalation(self, alert: HealthAlert) -> None:
        """Deliver an escalated health alert to stakeholders."""
        raise NotImplementedError