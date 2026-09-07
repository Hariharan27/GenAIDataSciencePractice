from ai_project_health_monitor.analysis.evidence_adapter import EvidenceAdapter
from ai_project_health_monitor.analysis.health_scorer import HealthScorer
from ai_project_health_monitor.analysis.risk_analyzer import RiskAnalyzer
from ai_project_health_monitor.analysis.risk_consolidator import RiskConsolidator
from ai_project_health_monitor.domain.models.health_score import HealthScore
from ai_project_health_monitor.rag.models.retrieval import RetrievalResult


class ProjectHealthService:
    """Coordinate evidence conversion, risk analysis, consolidation, and scoring."""

    def __init__(
        self,
        risk_analyzer: RiskAnalyzer,
        health_scorer: HealthScorer,
        risk_consolidator: RiskConsolidator,
    ) -> None:
        self._risk_analyzer = risk_analyzer
        self._health_scorer = health_scorer
        self._risk_consolidator = risk_consolidator

    def analyze(
        self,
        project_id: str,
        query: str,
        retrieval_results: list[RetrievalResult],
    ) -> HealthScore:
        """Analyze project health using evidence relevant to a query."""
        if not project_id.strip():
            raise ValueError("project_id cannot be empty")

        if not query.strip():
            raise ValueError("query cannot be empty")

        evidence = EvidenceAdapter.from_retrieval_results(
            retrieval_results
        )

        risk_signals = self._risk_analyzer.analyze(
            project_id=project_id,
            query=query,
            evidence=evidence,
        )

        risk_groups = self._risk_consolidator.consolidate(
            risk_signals
        )

        primary_risks = self._risk_consolidator.primary_risks(
            risk_groups
        )

        return self._health_scorer.calculate(
            project_id=project_id,
            risk_signals=primary_risks,
        )