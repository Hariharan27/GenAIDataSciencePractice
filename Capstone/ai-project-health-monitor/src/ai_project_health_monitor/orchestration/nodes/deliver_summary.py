from ai_project_health_monitor.notifications.health_summary_notifier import (
    HealthSummaryNotifier,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState


class DeliverSummaryNode:
    """Delivers the generated project health summary."""

    def __init__(self, summary_notifier: HealthSummaryNotifier) -> None:
        self._summary_notifier = summary_notifier

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        if state.summary is None:
            raise ValueError("summary must be available before delivering summary")

        self._summary_notifier.notify(state.summary)

        return {}