from unittest.mock import Mock

from ai_project_health_monitor.domain.models.project_health_summary import (
    ProjectHealthSummary,
)
from ai_project_health_monitor.notifications.health_summary_delivery import (
    HealthSummaryDelivery,
)
from ai_project_health_monitor.notifications.logging_health_summary_notifier import (
    LoggingHealthSummaryNotifier,
)


def test_logging_health_summary_notifier_delegates_to_delivery() -> None:
    delivery = Mock(spec=HealthSummaryDelivery)

    summary = Mock(spec=ProjectHealthSummary)

    notifier = LoggingHealthSummaryNotifier(delivery=delivery)

    notifier.notify(summary)

    delivery.deliver.assert_called_once_with(summary)