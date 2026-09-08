from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.notifications.deterministic_alert_escalator import (
    DeterministicAlertEscalator,
)


def test_escalates_triggered_critical_alert() -> None:
    alert = HealthAlert(
        project_id="PROJ-001",
        health_score=30.0,
        health_status=HealthStatus.CRITICAL,
        message="Immediate attention is required.",
        triggered=True,
    )

    escalator = DeterministicAlertEscalator()

    assert escalator.should_escalate(alert) is True


def test_does_not_escalate_non_critical_alert() -> None:
    alert = HealthAlert(
        project_id="PROJ-001",
        health_score=60.0,
        health_status=HealthStatus.AT_RISK,
        message="No critical alert required.",
        triggered=False,
    )

    escalator = DeterministicAlertEscalator()

    assert escalator.should_escalate(alert) is False