from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.notifications.alert_deduplicator import (
    AlertDeduplicator,
)


class DeterministicAlertDeduplicator(AlertDeduplicator):
    """Prevents repeated notifications for the same active critical alert."""

    def __init__(self) -> None:
        self._notified_alerts: set[str] = set()

    def should_notify(self, alert: HealthAlert) -> bool:
        """Return True only when this alert has not already been notified."""
        alert_key = self._build_alert_key(alert)

        if alert_key in self._notified_alerts:
            return False

        self._notified_alerts.add(alert_key)
        return True

    @staticmethod
    def _build_alert_key(alert: HealthAlert) -> str:
        return (
            f"{alert.project_id}:"
            f"{alert.health_status.value}:"
            f"{alert.health_score:.1f}"
        )