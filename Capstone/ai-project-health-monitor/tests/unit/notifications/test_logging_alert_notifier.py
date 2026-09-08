import logging

from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.notifications.logging_alert_notifier import (
    LoggingAlertNotifier,
)


def test_logging_alert_notifier_logs_health_alert(
    caplog,
) -> None:
    alert = HealthAlert(
        project_id="PROJ-001",
        health_score=30.0,
        health_status=HealthStatus.CRITICAL,
        message="Immediate attention is required.",
        triggered=True,
    )

    notifier = LoggingAlertNotifier()

    with caplog.at_level(logging.WARNING):
        notifier.notify(alert)

    assert "PROJECT HEALTH ALERT" in caplog.text
    assert "project_id=PROJ-001" in caplog.text
    assert "health_score=30.0" in caplog.text
    assert "health_status=critical" in caplog.text
    assert "Immediate attention is required." in caplog.text