from ai_project_health_monitor.notifications.alert_escalator_notifier import (
    AlertEscalatorNotifier,
)


def test_alert_escalator_notifier_defines_notify_escalation_contract() -> None:
    assert hasattr(AlertEscalatorNotifier, "notify_escalation")