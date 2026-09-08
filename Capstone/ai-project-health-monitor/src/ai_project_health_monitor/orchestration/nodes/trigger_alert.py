from ai_project_health_monitor.notifications.alert_deduplicator import (
    AlertDeduplicator,
)
from ai_project_health_monitor.notifications.alert_notifier import AlertNotifier
from ai_project_health_monitor.orchestration.state import ProjectHealthState


class TriggerAlertNode:
    """Executes the alert action for a triggered health alert."""

    def __init__(
        self,
        notifier: AlertNotifier,
        deduplicator: AlertDeduplicator,
    ) -> None:
        self._notifier = notifier
        self._deduplicator = deduplicator

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        if state.alert is None:
            raise ValueError("alert must be available before triggering alert")

        if not state.alert.triggered:
            raise ValueError(
                "cannot trigger an alert when alert.triggered is False"
            )

        if self._deduplicator.should_notify(state.alert):
            self._notifier.notify(state.alert)

        return {"alert_triggered": True}