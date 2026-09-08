from ai_project_health_monitor.analysis.health_alert_evaluator import (
    HealthAlertEvaluator,
)
from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.domain.models.health_score import (
    HealthScore,
    HealthStatus,
)


class DeterministicHealthAlertEvaluator(HealthAlertEvaluator):
    """Deterministically evaluates whether project health requires an alert."""

    def evaluate(self, health_score: HealthScore) -> HealthAlert:
        triggered = health_score.status == HealthStatus.CRITICAL

        message = self._build_message(
            health_score=health_score,
            triggered=triggered,
        )

        return HealthAlert(
            project_id=health_score.project_id,
            health_score=health_score.score,
            health_status=health_score.status,
            message=message,
            triggered=triggered,
        )

    @staticmethod
    def _build_message(
        health_score: HealthScore,
        triggered: bool,
    ) -> str:
        if triggered:
            return (
                f"Project {health_score.project_id} health is critical "
                f"with a score of {health_score.score:.1f}/100. "
                "Immediate attention is required."
            )

        return (
            f"Project {health_score.project_id} does not require a critical alert. "
            f"Current health score is {health_score.score:.1f}/100 "
            f"with status {health_score.status.value}."
        )