from langgraph import graph
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ai_project_health_monitor.analysis.health_scorer import HealthScorer
from ai_project_health_monitor.analysis.health_summary_generator import HealthSummaryGenerator
from ai_project_health_monitor.analysis.llm_risk_analyzer import LLMRiskAnalyzer
from ai_project_health_monitor.analysis.risk_analyzer import RiskAnalyzer
from ai_project_health_monitor.analysis.risk_consolidator import RiskConsolidator
from ai_project_health_monitor.notifications.alert_deduplicator import AlertDeduplicator
from ai_project_health_monitor.notifications.alert_escalator import AlertEscalator
from ai_project_health_monitor.notifications.alert_escalator_notifier import AlertEscalatorNotifier
from ai_project_health_monitor.notifications.health_summary_notifier import HealthSummaryNotifier
from ai_project_health_monitor.orchestration.nodes.analyze_risks import (
    AnalyzeRisksNode,
)
from ai_project_health_monitor.orchestration.nodes.calculate_health import (
    CalculateHealthNode,
)
from ai_project_health_monitor.orchestration.nodes.consolidate_risks import (
    ConsolidateRisksNode,
)
from ai_project_health_monitor.orchestration.nodes.generate_summary import GenerateSummaryNode
from ai_project_health_monitor.orchestration.nodes.retrieve import RetrieveNode
from ai_project_health_monitor.orchestration.nodes.trigger_alert import TriggerAlertNode
from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.rag.retrieval import RetrievalService
from ai_project_health_monitor.analysis.health_alert_evaluator import (
    HealthAlertEvaluator,
)
from ai_project_health_monitor.orchestration.nodes.evaluate_alert import (
    EvaluateAlertNode,
)
from ai_project_health_monitor.notifications.alert_notifier import AlertNotifier
from ai_project_health_monitor.orchestration.nodes.deliver_summary import (
    DeliverSummaryNode,
)


def route_after_alert_evaluation(
    state: ProjectHealthState,
) -> str:
    if state.alert is None:
        raise ValueError("alert must be available before routing")

    if state.alert.triggered:
        return "alert"

    return END


def build_project_health_graph(
    retrieval_service: RetrievalService,
    risk_analyzer: RiskAnalyzer,
    risk_consolidator: RiskConsolidator,
    health_scorer: HealthScorer,
    summary_generator: HealthSummaryGenerator,
    alert_evaluator: HealthAlertEvaluator,
    notifier: AlertNotifier,
    deduplicator: AlertDeduplicator,
    escalator: AlertEscalator,
    escalation_notifier: AlertEscalatorNotifier,
    summary_notifier: HealthSummaryNotifier,
) -> CompiledStateGraph[ProjectHealthState, None, ProjectHealthState, ProjectHealthState]:
    """Build and compile the project health analysis workflow."""

    retrieve_node = RetrieveNode(
        retrieval_service=retrieval_service,
    )

    analyze_risks_node = AnalyzeRisksNode(
        risk_analyzer=risk_analyzer,
    )

    consolidate_risks_node = ConsolidateRisksNode(
        risk_consolidator=risk_consolidator,
    )

    calculate_health_node = CalculateHealthNode(
        health_scorer=health_scorer,
    )

    generate_summary_node = GenerateSummaryNode(
        summary_generator=summary_generator,
    )

    evaluate_alert_node = EvaluateAlertNode(
        alert_evaluator=alert_evaluator,
    )

    trigger_alert = TriggerAlertNode(
        notifier=notifier,
        deduplicator=deduplicator,
        escalator=escalator,
        escalation_notifier=escalation_notifier,
    )

    deliver_summary_node = DeliverSummaryNode(
    summary_notifier=summary_notifier,
    )

    graph = StateGraph(ProjectHealthState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("analyze_risks", analyze_risks_node)
    graph.add_node("consolidate_risks", consolidate_risks_node)
    graph.add_node("calculate_health", calculate_health_node)
    graph.add_node("generate_summary", generate_summary_node)
    graph.add_node("evaluate_alert", evaluate_alert_node)
    graph.add_node("alert", trigger_alert)
    graph.add_node("deliver_summary", deliver_summary_node)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "analyze_risks")
    graph.add_edge("analyze_risks", "consolidate_risks")
    graph.add_edge("consolidate_risks", "calculate_health")
    graph.add_edge("calculate_health", "generate_summary")
    graph.add_edge("generate_summary", "deliver_summary")
    graph.add_edge("deliver_summary", "evaluate_alert")
    graph.add_conditional_edges(
        "evaluate_alert",
        route_after_alert_evaluation,
        {
            "alert": "alert",
            END: END,
        },
    )
    graph.add_edge("alert", END)

    return graph.compile()