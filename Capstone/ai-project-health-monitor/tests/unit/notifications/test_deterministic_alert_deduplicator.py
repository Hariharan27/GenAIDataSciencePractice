from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.notifications.deterministic_alert_deduplicator import (
    DeterministicAlertDeduplicator,
)


def test_deduplicator_allows_first_alert() -> None:
    alert = HealthAlert(
        project_id="PROJ-001",
        health_score=30.0,
        health_status=HealthStatus.CRITICAL,
        message="Immediate attention is required.",
        triggered=True,
    )

    deduplicator = DeterministicAlertDeduplicator()

    assert deduplicator.should_notify(alert) is True


def test_deduplicator_suppresses_duplicate_alert() -> None:
    alert = HealthAlert(
        project_id="PROJ-001",
        health_score=30.0,
        health_status=HealthStatus.CRITICAL,
        message="Immediate attention is required.",
        triggered=True,
    )

    deduplicator = DeterministicAlertDeduplicator()

    assert deduplicator.should_notify(alert) is True
    assert deduplicator.should_notify(alert) is False


def test_deduplicator_allows_alert_when_health_changes() -> None:
    first_alert = HealthAlert(
        project_id="PROJ-001",
        health_score=30.0,
        health_status=HealthStatus.CRITICAL,
        message="Immediate attention is required.",
        triggered=True,
    )

    changed_alert = HealthAlert(
        project_id="PROJ-001",
        health_score=25.0,
        health_status=HealthStatus.CRITICAL,
        message="Immediate attention is required.",
        triggered=True,
    )

    deduplicator = DeterministicAlertDeduplicator()

    assert deduplicator.should_notify(first_alert) is True
    assert deduplicator.should_notify(changed_alert) is True