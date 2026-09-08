from unittest.mock import Mock

from ai_project_health_monitor.analysis.health_alert_evaluator import HealthAlertEvaluator
from ai_project_health_monitor.analysis.health_scorer import HealthScorer
from ai_project_health_monitor.analysis.llm_risk_analyzer import LLMRiskAnalyzer
from ai_project_health_monitor.analysis.risk_consolidator import RiskConsolidator
from ai_project_health_monitor.orchestration.graph import (
    build_project_health_graph,
)
from ai_project_health_monitor.rag.retrieval import RetrievalService
from ai_project_health_monitor.analysis.health_summary_generator import (
    HealthSummaryGenerator,
)
from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.orchestration.graph import (
    build_project_health_graph,
    route_after_alert_evaluation,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.notifications.alert_notifier import AlertNotifier
from ai_project_health_monitor.notifications.alert_deduplicator import (
    AlertDeduplicator,
)


def test_project_health_graph_can_be_compiled() -> None:
    retrieval_service = Mock(spec=RetrievalService)
    risk_analyzer = Mock(spec=LLMRiskAnalyzer)
    risk_consolidator = Mock(spec=RiskConsolidator)
    health_scorer = Mock(spec=HealthScorer)
    summary_generator = Mock(spec=HealthSummaryGenerator)
    notifier = Mock(spec=AlertNotifier)
    deduplicator = Mock(spec=AlertDeduplicator)

    graph = build_project_health_graph(
        retrieval_service=retrieval_service,
        risk_analyzer=risk_analyzer,
        risk_consolidator=risk_consolidator,
        health_scorer=health_scorer,
        summary_generator=summary_generator,
        alert_evaluator = Mock(spec=HealthAlertEvaluator),
        notifier=notifier,
        deduplicator=deduplicator,
    )

    assert graph is not None

def test_route_after_alert_evaluation_routes_critical_alert_to_alert() -> None:
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What is the project health?",
        alert=HealthAlert(
            project_id="PROJ-001",
            health_score=35.0,
            health_status=HealthStatus.CRITICAL,
            message="Immediate attention is required.",
            triggered=True,
        ),
    )

    assert route_after_alert_evaluation(state) == "alert"


def test_route_after_alert_evaluation_routes_non_critical_alert_to_end() -> None:
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What is the project health?",
        alert=HealthAlert(
            project_id="PROJ-001",
            health_score=60.0,
            health_status=HealthStatus.AT_RISK,
            message="No critical alert required.",
            triggered=False,
        ),
    )

    assert route_after_alert_evaluation(state) == "__end__"

def test_route_after_alert_evaluation_requires_alert() -> None:
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What is the project health?",
    )

    try:
        route_after_alert_evaluation(state)
    except ValueError as exc:
        assert str(exc) == "alert must be available before routing"
    else:
        raise AssertionError("Expected ValueError")