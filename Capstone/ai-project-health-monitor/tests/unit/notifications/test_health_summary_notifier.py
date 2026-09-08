from ai_project_health_monitor.notifications.health_summary_notifier import (
    HealthSummaryNotifier,
)


def test_health_summary_notifier_defines_notify_contract() -> None:
    assert hasattr(HealthSummaryNotifier, "notify")