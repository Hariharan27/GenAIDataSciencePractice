from ai_project_health_monitor.notifications.alert_delivery import AlertDelivery


def test_alert_delivery_defines_deliver_contract() -> None:
    assert hasattr(AlertDelivery, "deliver")