from datetime import datetime, timezone
from unittest.mock import Mock

from ai_project_health_monitor.analysis.health_alert_evaluator import HealthAlertEvaluator
from ai_project_health_monitor.analysis.health_scorer import HealthScorer
from ai_project_health_monitor.analysis.health_summary_generator import (
    HealthSummaryGenerator,
)
from ai_project_health_monitor.analysis.llm_risk_analyzer import LLMRiskAnalyzer
from ai_project_health_monitor.analysis.risk_consolidator import RiskConsolidator
from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.domain.models.health_score import HealthScore, HealthStatus
from ai_project_health_monitor.notifications.alert_deduplicator import (
    AlertDeduplicator,
)
from ai_project_health_monitor.notifications.alert_escalator import AlertEscalator
from ai_project_health_monitor.notifications.alert_escalator_notifier import AlertEscalatorNotifier
from ai_project_health_monitor.notifications.alert_notifier import AlertNotifier
from ai_project_health_monitor.notifications.health_summary_notifier import HealthSummaryNotifier
from ai_project_health_monitor.orchestration.graph import (
    build_project_health_graph,
    route_after_alert_evaluation,
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
from ai_project_health_monitor.ingestion.service import IngestionService
from ai_project_health_monitor.domain.models.project_health_summary import (
    ProjectHealthSummary,
)
from ai_project_health_monitor.persistence.health_snapshot import (
    ProjectHealthSnapshot,
)
from ai_project_health_monitor.domain.models.project_event import (
    ProjectEvent,
    SourceType,
)
from ai_project_health_monitor.analysis.risk_change_investigator import (
    RiskChangeInvestigator,
)


def test_project_health_graph_can_be_compiled() -> None:
    retrieval_service = Mock(spec=ProjectHealthEvidenceRetriever)
    risk_analyzer = Mock(spec=LLMRiskAnalyzer)
    risk_consolidator = Mock(spec=RiskConsolidator)
    risk_change_investigator = Mock(spec=RiskChangeInvestigator)
    health_scorer = Mock(spec=HealthScorer)
    summary_generator = Mock(spec=HealthSummaryGenerator)
    notifier = Mock(spec=AlertNotifier)
    deduplicator = Mock(spec=AlertDeduplicator)
    escalator = Mock(spec=AlertEscalator)
    escalation_notifier = Mock(spec=AlertEscalatorNotifier)

    summary_notifier = Mock(spec=HealthSummaryNotifier)
    health_snapshot_repository = Mock(spec=HealthSnapshotRepository)
    risk_change_detector = Mock(spec=RiskChangeDetector)
    ingestion_service = Mock(spec=IngestionService)

    graph = build_project_health_graph(
        evidence_retriever=retrieval_service,
        risk_analyzer=risk_analyzer,
        risk_consolidator=risk_consolidator,
        risk_change_detector=risk_change_detector,
        risk_change_investigator=risk_change_investigator,
        health_scorer=health_scorer,
        summary_generator=summary_generator,
        alert_evaluator = Mock(spec=HealthAlertEvaluator),
        notifier=notifier,
        deduplicator=deduplicator,
        escalator=escalator,
        escalation_notifier=escalation_notifier,
        summary_notifier=summary_notifier,
        health_snapshot_repository=health_snapshot_repository,
        ingestion_service=ingestion_service,
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

def test_project_health_graph_runs_risk_change_investigation() -> None:
    retrieval_service = Mock(spec=ProjectHealthEvidenceRetriever)
    risk_analyzer = Mock(spec=LLMRiskAnalyzer)
    risk_consolidator = Mock(spec=RiskConsolidator)
    health_scorer = Mock(spec=HealthScorer)
    summary_generator = Mock(spec=HealthSummaryGenerator)
    alert_evaluator = Mock(spec=HealthAlertEvaluator)
    notifier = Mock(spec=AlertNotifier)
    deduplicator = Mock(spec=AlertDeduplicator)
    escalator = Mock(spec=AlertEscalator)
    escalation_notifier = Mock(spec=AlertEscalatorNotifier)
    summary_notifier = Mock(spec=HealthSummaryNotifier)
    health_snapshot_repository = Mock(spec=HealthSnapshotRepository)
    health_snapshot_repository.get_latest.return_value = None
    risk_change_detector = Mock(spec=RiskChangeDetector)
    ingestion_service = Mock(spec=IngestionService)
    risk_change_investigator = Mock(spec=RiskChangeInvestigator)
    risk_change_investigator.investigate.return_value = []

    ingestion_service.ingest_project.return_value = []

    retrieval_service.retrieve.return_value = []

    risk_analyzer.analyze.return_value = []

    risk_consolidator.consolidate.return_value = []
    risk_consolidator.primary_risks.return_value = []

    health_scorer.calculate.return_value = HealthScore(
        project_id="PROJ-001",
        score=100.0,
        status=HealthStatus.HEALTHY,
        contributing_risks=[],
        calculated_at=datetime.now(timezone.utc),
        rationale="Test health score.",
    )

    summary_generator.generate.return_value = ProjectHealthSummary(
        project_id="PROJ-001",
        health_score=100.0,
        health_status=HealthStatus.HEALTHY,
        executive_summary="Project is healthy.",
    )

    alert_evaluator.evaluate.return_value = HealthAlert(
        project_id="PROJ-001",
        health_score=100.0,
        health_status=HealthStatus.HEALTHY,
        message="Project is healthy.",
        triggered=False,
    )

    risk_change_detector.detect.return_value = []

    graph = build_project_health_graph(
        evidence_retriever=retrieval_service,
        risk_analyzer=risk_analyzer,
        risk_consolidator=risk_consolidator,
        risk_change_detector=risk_change_detector,
        risk_change_investigator=risk_change_investigator,
        health_scorer=health_scorer,
        summary_generator=summary_generator,
        alert_evaluator=alert_evaluator,
        notifier=notifier,
        deduplicator=deduplicator,
        escalator=escalator,
        escalation_notifier=escalation_notifier,
        summary_notifier=summary_notifier,
        health_snapshot_repository=health_snapshot_repository,
        ingestion_service=ingestion_service,
    )

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What is the project health?",
    )

    graph.invoke(state)

    risk_change_detector.detect.assert_called_once()

def test_project_health_graph_returns_previous_health_when_evidence_is_unchanged() -> None:
    retrieval_service = Mock(spec=ProjectHealthEvidenceRetriever)
    risk_analyzer = Mock(spec=LLMRiskAnalyzer)
    risk_consolidator = Mock(spec=RiskConsolidator)
    risk_change_investigator = Mock(spec=RiskChangeInvestigator)
    health_scorer = Mock(spec=HealthScorer)
    summary_generator = Mock(spec=HealthSummaryGenerator)
    alert_evaluator = Mock(spec=HealthAlertEvaluator)
    notifier = Mock(spec=AlertNotifier)
    deduplicator = Mock(spec=AlertDeduplicator)
    escalator = Mock(spec=AlertEscalator)
    escalation_notifier = Mock(spec=AlertEscalatorNotifier)
    summary_notifier = Mock(spec=HealthSummaryNotifier)
    health_snapshot_repository = Mock(spec=HealthSnapshotRepository)
    risk_change_detector = Mock(spec=RiskChangeDetector)
    ingestion_service = Mock(spec=IngestionService)

    previous_snapshot = ProjectHealthSnapshot(
        project_id="PROJ-001",
        health_score=81.0,
        health_status=HealthStatus.HEALTHY,
        risk_signals=[],
        evidence_fingerprint="4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
        calculated_at=datetime.now(timezone.utc),
    )

    health_snapshot_repository.get_latest.return_value = previous_snapshot

    ingestion_service.ingest_project.return_value = []

    graph = build_project_health_graph(
        evidence_retriever=retrieval_service,
        risk_analyzer=risk_analyzer,
        risk_consolidator=risk_consolidator,
        risk_change_detector=risk_change_detector,
        risk_change_investigator=risk_change_investigator,
        health_scorer=health_scorer,
        summary_generator=summary_generator,
        alert_evaluator=alert_evaluator,
        notifier=notifier,
        deduplicator=deduplicator,
        escalator=escalator,
        escalation_notifier=escalation_notifier,
        summary_notifier=summary_notifier,
        health_snapshot_repository=health_snapshot_repository,
        ingestion_service=ingestion_service,
    )

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What is the project health?",
    )

    result = graph.invoke(state)

    assert result["health_score"].score == 81.0
    assert result["health_score"].status == HealthStatus.HEALTHY

    retrieval_service.retrieve.assert_not_called()
    risk_analyzer.analyze.assert_not_called()
    risk_change_detector.detect.assert_not_called()
    health_scorer.calculate.assert_not_called()

def test_project_health_graph_investigates_risk_changes_when_evidence_changes() -> None:
    retrieval_service = Mock(spec=ProjectHealthEvidenceRetriever)
    risk_analyzer = Mock(spec=LLMRiskAnalyzer)
    risk_consolidator = Mock(spec=RiskConsolidator)
    risk_change_detector = Mock(spec=RiskChangeDetector)
    risk_change_investigator = Mock(spec=RiskChangeInvestigator)
    risk_change_investigator.investigate.return_value = []
    health_scorer = Mock(spec=HealthScorer)
    summary_generator = Mock(spec=HealthSummaryGenerator)
    alert_evaluator = Mock(spec=HealthAlertEvaluator)
    notifier = Mock(spec=AlertNotifier)
    deduplicator = Mock(spec=AlertDeduplicator)
    escalator = Mock(spec=AlertEscalator)
    escalation_notifier = Mock(spec=AlertEscalatorNotifier)
    summary_notifier = Mock(spec=HealthSummaryNotifier)
    health_snapshot_repository = Mock(spec=HealthSnapshotRepository)
    risk_change_detector = Mock(spec=RiskChangeDetector)
    ingestion_service = Mock(spec=IngestionService)

    previous_snapshot = ProjectHealthSnapshot(
        project_id="PROJ-001",
        health_score=81.0,
        health_status=HealthStatus.HEALTHY,
        risk_signals=[],
        evidence_fingerprint="previous-fingerprint",
        calculated_at=datetime.now(timezone.utc),
    )

    health_snapshot_repository.get_latest.return_value = previous_snapshot

    ingestion_service.ingest_project.return_value = [
        ProjectEvent(
            event_id="EVT-002",
            project_id="PROJ-001",
            source_type=SourceType.JIRA,
            source_id="JIRA-002",
            content="A new project update was received.",
            author="test-user",
            occurred_at=datetime.now(timezone.utc),
            metadata={},
        )
    ]
    retrieval_service.retrieve.return_value = []
    risk_analyzer.analyze.return_value = []
    risk_consolidator.consolidate.return_value = []
    risk_consolidator.primary_risks.return_value = []

    health_scorer.calculate.return_value = HealthScore(
        project_id="PROJ-001",
        score=75.0,
        status=HealthStatus.HEALTHY,
        contributing_risks=[],
        calculated_at=datetime.now(timezone.utc),
        rationale="Test health score after evidence change.",
    )

    summary_generator.generate.return_value = ProjectHealthSummary(
        project_id="PROJ-001",
        health_score=75.0,
        health_status=HealthStatus.HEALTHY,
        executive_summary="Project remains healthy after the evidence change.",
    )

    alert_evaluator.evaluate.return_value = HealthAlert(
        project_id="PROJ-001",
        health_score=75.0,
        health_status=HealthStatus.HEALTHY,
        message="Project remains healthy.",
        triggered=False,
    )

    risk_change_detector.detect.return_value = []

    graph = build_project_health_graph(
        evidence_retriever=retrieval_service,
        risk_analyzer=risk_analyzer,
        risk_consolidator=risk_consolidator,
        risk_change_detector=risk_change_detector,
        risk_change_investigator=risk_change_investigator,
        health_scorer=health_scorer,
        summary_generator=summary_generator,
        alert_evaluator=alert_evaluator,
        notifier=notifier,
        deduplicator=deduplicator,
        escalator=escalator,
        escalation_notifier=escalation_notifier,
        summary_notifier=summary_notifier,
        health_snapshot_repository=health_snapshot_repository,
        ingestion_service=ingestion_service,
    )

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What is the project health?",
    )

    graph.invoke(state)

    retrieval_service.retrieve.assert_called_once()
    risk_analyzer.analyze.assert_called_once()
    risk_change_detector.detect.assert_called_once()
    risk_change_investigator.investigate.assert_called_once()