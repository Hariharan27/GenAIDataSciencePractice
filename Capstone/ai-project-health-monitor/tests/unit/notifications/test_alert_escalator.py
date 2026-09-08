from ai_project_health_monitor.notifications.alert_escalator import AlertEscalator


def test_alert_escalator_defines_should_escalate_contract() -> None:
    assert hasattr(AlertEscalator, "should_escalate")