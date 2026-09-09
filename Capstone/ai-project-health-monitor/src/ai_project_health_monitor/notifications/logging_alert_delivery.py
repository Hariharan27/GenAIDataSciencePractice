import logging

from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.notifications.alert_delivery import AlertDelivery

logger = logging.getLogger(__name__)


class LoggingAlertDelivery(AlertDelivery):
    """Delivers project health alerts through application logging."""

    def deliver(self, alert: HealthAlert) -> None:
        logger.warning(
            "PROJECT HEALTH ALERT DELIVERY | project_id=%s "
            "| health_score=%.1f | health_status=%s | message=%s",
            alert.project_id,
            alert.health_score,
            alert.health_status.value,
            alert.message,
        )