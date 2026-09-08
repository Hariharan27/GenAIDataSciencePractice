from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.notifications.alert_delivery import AlertDelivery
from ai_project_health_monitor.notifications.alert_notifier import AlertNotifier


class LoggingAlertNotifier(AlertNotifier):
    """Coordinates delivery of project health alerts."""

    def __init__(self, delivery: AlertDelivery) -> None:
        self._delivery = delivery

    def notify(self, alert: HealthAlert) -> None:
        self._delivery.deliver(alert)