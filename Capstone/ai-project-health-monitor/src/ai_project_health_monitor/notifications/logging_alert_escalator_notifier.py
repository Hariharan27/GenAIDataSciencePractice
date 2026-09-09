import logging

from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.notifications.alert_escalator_notifier import (
    AlertEscalatorNotifier,
)

logger = logging.getLogger(__name__)


class LoggingAlertEscalatorNotifier(AlertEscalatorNotifier):
    """Delivers escalated project health alerts through application logging."""

    def notify_escalation(self, alert: HealthAlert) -> None:
        logger.critical(
            "PROJECT HEALTH ALERT ESCALATION | project_id=%s "
            "| health_score=%.1f | health_status=%s | message=%s",
            alert.project_id,
            alert.health_score,
            alert.health_status.value,
            alert.message,
        )