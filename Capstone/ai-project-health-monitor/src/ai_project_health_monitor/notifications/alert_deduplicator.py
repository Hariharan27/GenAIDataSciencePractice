from abc import ABC, abstractmethod

from ai_project_health_monitor.domain.models.health_alert import HealthAlert


class AlertDeduplicator(ABC):
    """Contract for preventing duplicate health alert notifications."""

    @abstractmethod
    def should_notify(self, alert: HealthAlert) -> bool:
        """Return whether the alert should be delivered."""
        raise NotImplementedError