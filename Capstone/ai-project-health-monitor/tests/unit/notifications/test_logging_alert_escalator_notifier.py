from unittest.mock import patch

from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.notifications.logging_alert_escalator_notifier import (
    LoggingAlertEscalatorNotifier,
)


def test_logging_alert_escalator_notifier_logs_escalated_alert() -> None:
    alert = HealthAlert(
        project_id="PROJ-001",
        health_score=30.0,
        health_status=HealthStatus.CRITICAL,
        message="Immediate attention is required.",
        triggered=True,
    )

    notifier = LoggingAlertEscalatorNotifier()

    with patch(
        "ai_project_health_monitor.notifications.logging_alert_escalator_notifier.logger"
    ) as logger:
        notifier.notify_escalation(alert)

    logger.critical.assert_called_once_with(
        "PROJECT HEALTH ALERT ESCALATION | project_id=%s "
        "| health_score=%.1f | health_status=%s | message=%s",
        "PROJ-001",
        30.0,
        "critical",
        "Immediate attention is required.",
    )