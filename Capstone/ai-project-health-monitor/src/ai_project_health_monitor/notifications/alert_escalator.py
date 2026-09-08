from abc import ABC, abstractmethod

from ai_project_health_monitor.domain.models.health_alert import HealthAlert


class AlertEscalator(ABC):
    """Contract for escalating critical project health alerts."""

    @abstractmethod
    def should_escalate(self, alert: HealthAlert) -> bool:
        """Return whether the alert requires escalation."""
        raise NotImplementedError