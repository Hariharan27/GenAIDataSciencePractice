from langgraph import graph
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ai_project_health_monitor.analysis.health_alert_evaluator import (
    HealthAlertEvaluator,
)
from ai_project_health_monitor.analysis.health_scorer import HealthScorer
from ai_project_health_monitor.analysis.health_summary_generator import (
    HealthSummaryGenerator,
)
from ai_project_health_monitor.analysis.llm_risk_change_investigator import LLMRiskChangeInvestigator
from ai_project_health_monitor.analysis.risk_analyzer import RiskAnalyzer
from ai_project_health_monitor.analysis.risk_consolidator import RiskConsolidator
from ai_project_health_monitor.ingestion.service import IngestionService
from ai_project_health_monitor.notifications.alert_deduplicator import (
    AlertDeduplicator,
)
from ai_project_health_monitor.notifications.alert_escalator import AlertEscalator
from ai_project_health_monitor.notifications.alert_escalator_notifier import (
    AlertEscalatorNotifier,
)
from ai_project_health_monitor.notifications.alert_notifier import AlertNotifier
from ai_project_health_monitor.notifications.health_summary_notifier import (
    HealthSummaryNotifier,
)
from ai_project_health_monitor.orchestration.nodes.analyze_risks import (
    AnalyzeRisksNode,
)
from ai_project_health_monitor.orchestration.nodes.calculate_health import (
    CalculateHealthNode,
)
from ai_project_health_monitor.orchestration.nodes.collect_current_evidence import (
    CollectCurrentEvidenceNode,
)
from ai_project_health_monitor.orchestration.nodes.consolidate_risks import (
    ConsolidateRisksNode,
)
from ai_project_health_monitor.orchestration.nodes.deliver_summary import (
    DeliverSummaryNode,
)
from ai_project_health_monitor.orchestration.nodes.detect_evidence_changes import (
    DetectEvidenceChangesNode,
)
from ai_project_health_monitor.orchestration.nodes.evaluate_alert import (
    EvaluateAlertNode,
)
from ai_project_health_monitor.orchestration.nodes.generate_summary import (
    GenerateSummaryNode,
)
from ai_project_health_monitor.orchestration.nodes.load_previous_health import (
    LoadPreviousHealthNode,
)
from ai_project_health_monitor.orchestration.nodes.persist_health_snapshot import (
    PersistHealthSnapshotNode,
)
from ai_project_health_monitor.orchestration.nodes.retrieve import RetrieveNode
from ai_project_health_monitor.orchestration.nodes.return_previous_health import (
    ReturnPreviousHealthNode,
)
from ai_project_health_monitor.orchestration.nodes.trigger_alert import (
    TriggerAlertNode,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.persistence.repositories.health_snapshot import (
    HealthSnapshotRepository,
)
from ai_project_health_monitor.rag.project_health_retrieval import (
    ProjectHealthEvidenceRetriever,
)
from ai_project_health_monitor.analysis.risk_change_detector import (
    RiskChangeDetector,
)
from ai_project_health_monitor.orchestration.nodes.investigate_risk_changes import (
    InvestigateRiskChangesNode,
)


def route_after_alert_evaluation(
    state: ProjectHealthState,
) -> str:
    if state.alert is None:
        raise ValueError("alert must be available before routing")

    if state.alert.triggered:
        return "alert"

    return END


def route_after_evidence_change_detection(
    state: ProjectHealthState,
) -> str:
    """Route unchanged projects to the previous-health path."""
    if state.evidence_changed:
        return "analyze"

    if state.previous_health_snapshot is None:
        raise ValueError(
            "previous_health_snapshot must exist when evidence is unchanged"
        )

    return "unchanged"


def build_project_health_graph(
    evidence_retriever: ProjectHealthEvidenceRetriever,
    risk_analyzer: RiskAnalyzer,
    risk_consolidator: RiskConsolidator,
    risk_change_detector: RiskChangeDetector,
    risk_change_investigator: LLMRiskChangeInvestigator,
    health_scorer: HealthScorer,
    summary_generator: HealthSummaryGenerator,
    alert_evaluator: HealthAlertEvaluator,
    notifier: AlertNotifier,
    deduplicator: AlertDeduplicator,
    escalator: AlertEscalator,
    escalation_notifier: AlertEscalatorNotifier,
    summary_notifier: HealthSummaryNotifier,
    health_snapshot_repository: HealthSnapshotRepository,
    ingestion_service: IngestionService,
) -> CompiledStateGraph[
    ProjectHealthState,
    None,
    ProjectHealthState,
    ProjectHealthState,
]:
    """Build and compile the project health analysis workflow."""

    retrieve_node = RetrieveNode(
        evidence_retriever=evidence_retriever,
    )

    analyze_risks_node = AnalyzeRisksNode(
        risk_analyzer=risk_analyzer,
    )

    investigate_risk_changes_node = InvestigateRiskChangesNode(
    risk_change_detector=risk_change_detector,
    risk_change_investigator=risk_change_investigator,
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

    persist_health_snapshot_node = PersistHealthSnapshotNode(
        health_snapshot_repository=health_snapshot_repository,
    )

    load_previous_health_node = LoadPreviousHealthNode(
        health_snapshot_repository=health_snapshot_repository,
    )

    collect_current_evidence_node = CollectCurrentEvidenceNode(
        ingestion_service=ingestion_service,
    )

    detect_evidence_changes_node = DetectEvidenceChangesNode()

    return_previous_health_node = ReturnPreviousHealthNode()

    graph = StateGraph(ProjectHealthState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("analyze_risks", analyze_risks_node)
    graph.add_node(
    "investigate_risk_changes",
    investigate_risk_changes_node,
    )
    graph.add_node("consolidate_risks", consolidate_risks_node)
    graph.add_node("calculate_health", calculate_health_node)
    graph.add_node("generate_summary", generate_summary_node)
    graph.add_node("evaluate_alert", evaluate_alert_node)
    graph.add_node("alert", trigger_alert)
    graph.add_node("deliver_summary", deliver_summary_node)
    graph.add_node("persist_health_snapshot", persist_health_snapshot_node)
    graph.add_node("load_previous_health", load_previous_health_node)
    graph.add_node(
        "collect_current_evidence",
        collect_current_evidence_node,
    )
    graph.add_node(
        "detect_evidence_changes",
        detect_evidence_changes_node,
    )
    graph.add_node(
        "return_previous_health",
        return_previous_health_node,
    )

    graph.add_edge(START, "load_previous_health")

    graph.add_edge(
        "load_previous_health",
        "collect_current_evidence",
    )

    graph.add_edge(
        "collect_current_evidence",
        "detect_evidence_changes",
    )

    graph.add_conditional_edges(
        "detect_evidence_changes",
        route_after_evidence_change_detection,
        {
            "analyze": "retrieve",
            "unchanged": "return_previous_health",
        },
    )

    graph.add_edge("return_previous_health", END)

    graph.add_edge("retrieve", "analyze_risks")
    graph.add_edge(
        "analyze_risks",
        "investigate_risk_changes",
    )
    graph.add_edge(
        "investigate_risk_changes",
        "consolidate_risks",
    )
    graph.add_edge("consolidate_risks", "calculate_health")
    graph.add_edge("calculate_health", "generate_summary")
    graph.add_edge("generate_summary", "deliver_summary")
    graph.add_edge("deliver_summary", "persist_health_snapshot")
    graph.add_edge("persist_health_snapshot", "evaluate_alert")

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