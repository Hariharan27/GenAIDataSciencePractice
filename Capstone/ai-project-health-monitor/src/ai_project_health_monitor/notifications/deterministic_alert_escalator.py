from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.notifications.alert_escalator import (
    AlertEscalator,
)


class DeterministicAlertEscalator(AlertEscalator):
    """Escalates only critical project health alerts."""

    def should_escalate(self, alert: HealthAlert) -> bool:
        """Return True when the alert represents critical project health."""
        return alert.triggered and alert.health_status == HealthStatus.CRITICAL