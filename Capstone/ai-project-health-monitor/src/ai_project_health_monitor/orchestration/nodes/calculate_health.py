from ai_project_health_monitor.analysis.health_scorer import HealthScorer
from ai_project_health_monitor.orchestration.state import ProjectHealthState


class CalculateHealthNode:
    """LangGraph node responsible for calculating project health."""

    def __init__(self, health_scorer: HealthScorer) -> None:
        self._health_scorer = health_scorer

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        health_score = self._health_scorer.calculate(
            project_id=state.project_id,
            risk_signals=state.primary_risks,
        )

        return {
            "health_score": health_score,
        }