from ai_project_health_monitor.analysis.evidence_adapter import EvidenceAdapter
from ai_project_health_monitor.analysis.risk_analyzer import RiskAnalyzer
from ai_project_health_monitor.orchestration.state import ProjectHealthState


class AnalyzeRisksNode:
    """LangGraph node responsible for extracting risks from retrieved evidence."""

    def __init__(self, risk_analyzer: RiskAnalyzer) -> None:
        self._risk_analyzer = risk_analyzer

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        evidence = EvidenceAdapter.from_retrieval_results(
            state.retrieval_results
        )

        risk_signals = self._risk_analyzer.analyze(
            project_id=state.project_id,
            query=state.query,
            evidence=evidence,
        )

        return {
            "evidence": evidence,
            "risk_signals": risk_signals,
        }