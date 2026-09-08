from ai_project_health_monitor.notifications.alert_deduplicator import (
    AlertDeduplicator,
)
from ai_project_health_monitor.notifications.alert_notifier import AlertNotifier
from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.notifications.alert_escalator import (
    AlertEscalator,
)
from ai_project_health_monitor.notifications.alert_escalator_notifier import (
    AlertEscalatorNotifier,
)


class TriggerAlertNode:
    """Executes the alert action for a triggered health alert."""

    def __init__(
        self,
        notifier: AlertNotifier,
        deduplicator: AlertDeduplicator,
        escalator: AlertEscalator,
        escalation_notifier: AlertEscalatorNotifier,
    ) -> None:
        self._notifier = notifier
        self._deduplicator = deduplicator
        self._escalator = escalator
        self._escalation_notifier = escalation_notifier

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        if state.alert is None:
            raise ValueError("alert must be available before triggering alert")

        if not state.alert.triggered:
            raise ValueError(
                "cannot trigger an alert when alert.triggered is False"
            )

        if self._deduplicator.should_notify(state.alert):
            self._notifier.notify(state.alert)

            if self._escalator.should_escalate(state.alert):
                self._escalation_notifier.notify_escalation(state.alert)

        return {"alert_triggered": True}