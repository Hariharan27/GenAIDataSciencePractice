from unittest.mock import Mock

from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.notifications.alert_delivery import AlertDelivery
from ai_project_health_monitor.notifications.logging_alert_notifier import (
    LoggingAlertNotifier,
)


def test_logging_alert_notifier_delegates_to_delivery() -> None:
    delivery = Mock(spec=AlertDelivery)

    alert = HealthAlert(
        project_id="PROJ-001",
        health_score=30.0,
        health_status=HealthStatus.CRITICAL,
        message="Immediate attention is required.",
        triggered=True,
    )

    notifier = LoggingAlertNotifier(delivery=delivery)

    notifier.notify(alert)

    delivery.deliver.assert_called_once_with(alert)