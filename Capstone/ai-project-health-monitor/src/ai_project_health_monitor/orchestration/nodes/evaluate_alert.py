from ai_project_health_monitor.analysis.health_alert_evaluator import (
    HealthAlertEvaluator,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState


class EvaluateAlertNode:
    def __init__(self, alert_evaluator: HealthAlertEvaluator) -> None:
        self._alert_evaluator = alert_evaluator

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        if state.health_score is None:
            raise ValueError("health_score must be available before evaluating alert")

        alert = self._alert_evaluator.evaluate(
            health_score=state.health_score,
        )

        return {"alert": alert}