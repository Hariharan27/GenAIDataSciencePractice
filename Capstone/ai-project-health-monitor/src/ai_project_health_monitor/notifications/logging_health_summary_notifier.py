from ai_project_health_monitor.domain.models.project_health_summary import (
    ProjectHealthSummary,
)
from ai_project_health_monitor.notifications.health_summary_delivery import (
    HealthSummaryDelivery,
)
from ai_project_health_monitor.notifications.health_summary_notifier import (
    HealthSummaryNotifier,
)


class LoggingHealthSummaryNotifier(HealthSummaryNotifier):
    """Coordinates delivery of project health summaries."""

    def __init__(self, delivery: HealthSummaryDelivery) -> None:
        self._delivery = delivery

    def notify(self, summary: ProjectHealthSummary) -> None:
        self._delivery.deliver(summary)