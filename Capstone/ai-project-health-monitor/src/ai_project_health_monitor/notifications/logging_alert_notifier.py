import logging

from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.notifications.alert_notifier import AlertNotifier


logger = logging.getLogger(__name__)


class LoggingAlertNotifier(AlertNotifier):
    """Delivers project health alerts through application logging."""

    def notify(self, alert: HealthAlert) -> None:
        logger.warning(
            "PROJECT HEALTH ALERT | project_id=%s | health_score=%.1f "
            "| health_status=%s | message=%s",
            alert.project_id,
            alert.health_score,
            alert.health_status.value,
            alert.message,
        )