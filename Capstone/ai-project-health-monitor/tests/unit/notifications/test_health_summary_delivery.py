from ai_project_health_monitor.notifications.health_summary_delivery import (
    HealthSummaryDelivery,
)


def test_health_summary_delivery_defines_deliver_contract() -> None:
    assert hasattr(HealthSummaryDelivery, "deliver")