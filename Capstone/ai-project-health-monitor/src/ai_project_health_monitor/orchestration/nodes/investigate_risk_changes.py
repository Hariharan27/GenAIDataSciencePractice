from ai_project_health_monitor.analysis.llm_risk_change_investigator import (
    LLMRiskChangeInvestigator,
)
from ai_project_health_monitor.analysis.risk_change_detector import (
    RiskChangeDetector,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState


class InvestigateRiskChangesNode:
    """Detect and investigate changes in project risks."""

    def __init__(
        self,
        risk_change_detector: RiskChangeDetector,
        risk_change_investigator: LLMRiskChangeInvestigator,
    ) -> None:
        self._risk_change_detector = risk_change_detector
        self._risk_change_investigator = risk_change_investigator

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        previous_risks = (
            state.previous_health_snapshot.risk_signals
            if state.previous_health_snapshot is not None
            else []
        )

        deterministic_changes = self._risk_change_detector.detect(
            previous_risks=previous_risks,
            current_risks=state.risk_signals,
        )

        investigated_changes = self._risk_change_investigator.investigate(
            project_id=state.project_id,
            previous_risks=previous_risks,
            current_risks=state.risk_signals,
            evidence=state.evidence,
        )

        return {
            "risk_changes": (
                investigated_changes
                if investigated_changes
                else deterministic_changes
            ),
        }