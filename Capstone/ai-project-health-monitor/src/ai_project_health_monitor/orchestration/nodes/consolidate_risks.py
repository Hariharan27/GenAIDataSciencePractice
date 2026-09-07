from ai_project_health_monitor.analysis.risk_consolidator import RiskConsolidator
from ai_project_health_monitor.orchestration.state import ProjectHealthState


class ConsolidateRisksNode:
    """LangGraph node responsible for consolidating extracted risk signals."""

    def __init__(self, risk_consolidator: RiskConsolidator) -> None:
        self._risk_consolidator = risk_consolidator

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        risk_groups = self._risk_consolidator.consolidate(
            state.risk_signals
        )

        primary_risks = self._risk_consolidator.primary_risks(
            risk_groups
        )

        return {
            "risk_groups": risk_groups,
            "primary_risks": primary_risks,
        }