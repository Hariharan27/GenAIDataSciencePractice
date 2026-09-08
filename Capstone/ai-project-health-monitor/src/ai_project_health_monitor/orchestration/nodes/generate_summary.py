from ai_project_health_monitor.analysis.health_summary_generator import (
    HealthSummaryGenerator,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState


class GenerateSummaryNode:
    def __init__(self, summary_generator: HealthSummaryGenerator) -> None:
        self._summary_generator = summary_generator

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        if state.health_score is None:
            raise ValueError("health_score must be available before generating summary")

        summary = self._summary_generator.generate(
            health_score=state.health_score,
            risk_signals=state.primary_risks,
        )

        return {"summary": summary}