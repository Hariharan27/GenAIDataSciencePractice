from unittest.mock import patch

from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.notifications.logging_alert_delivery import (
    LoggingAlertDelivery,
)


def test_logging_alert_delivery_logs_alert() -> None:
    alert = HealthAlert(
        project_id="PROJ-001",
        health_score=30.0,
        health_status=HealthStatus.CRITICAL,
        message="Immediate attention is required.",
        triggered=True,
    )

    delivery = LoggingAlertDelivery()

    with patch(
        "ai_project_health_monitor.notifications.logging_alert_delivery.logger"
    ) as logger:
        delivery.deliver(alert)

    logger.warning.assert_called_once_with(
        "PROJECT HEALTH ALERT DELIVERY | project_id=%s "
        "| health_score=%.1f | health_status=%s | message=%s",
        "PROJ-001",
        30.0,
        "critical",
        "Immediate attention is required.",
    )