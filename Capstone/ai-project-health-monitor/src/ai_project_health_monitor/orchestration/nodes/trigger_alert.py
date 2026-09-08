from ai_project_health_monitor.orchestration.state import ProjectHealthState


class TriggerAlertNode:
    """Executes the alert action for a triggered health alert."""

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        if state.alert is None:
            raise ValueError("alert must be available before triggering alert")

        if not state.alert.triggered:
            raise ValueError(
                "cannot trigger an alert when alert.triggered is False"
            )

        return {"alert_triggered": True}