from unittest.mock import Mock

from ai_project_health_monitor.analysis.health_scorer import HealthScorer
from ai_project_health_monitor.analysis.llm_risk_analyzer import LLMRiskAnalyzer
from ai_project_health_monitor.analysis.risk_consolidator import RiskConsolidator
from ai_project_health_monitor.orchestration.graph import (
    build_project_health_graph,
)
from ai_project_health_monitor.rag.retrieval import RetrievalService


def test_project_health_graph_can_be_compiled() -> None:
    retrieval_service = Mock(spec=RetrievalService)
    risk_analyzer = Mock(spec=LLMRiskAnalyzer)
    risk_consolidator = Mock(spec=RiskConsolidator)
    health_scorer = Mock(spec=HealthScorer)

    graph = build_project_health_graph(
        retrieval_service=retrieval_service,
        risk_analyzer=risk_analyzer,
        risk_consolidator=risk_consolidator,
        health_scorer=health_scorer,
    )

    assert graph is not None