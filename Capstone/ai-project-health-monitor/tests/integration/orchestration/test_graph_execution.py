from datetime import UTC, datetime
from unittest.mock import Mock

from ai_project_health_monitor.analysis.deterministic_health_scorer import (
    DeterministicHealthScorer,
)
from ai_project_health_monitor.analysis.health_alert_evaluator import (
    HealthAlertEvaluator,
)
from ai_project_health_monitor.analysis.health_scorer import HealthScorer
from ai_project_health_monitor.analysis.health_summary_generator import (
    HealthSummaryGenerator,
)
from ai_project_health_monitor.analysis.llm_risk_analyzer import LLMRiskAnalyzer
from ai_project_health_monitor.analysis.risk_consolidator import RiskConsolidator
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.domain.models.health_score import (
    HealthScore,
    HealthStatus,
)
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.project_health_summary import (
    ProjectHealthSummary,
)
from ai_project_health_monitor.domain.models.risk_group import RiskGroup
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)
from ai_project_health_monitor.notifications.alert_deduplicator import AlertDeduplicator
from ai_project_health_monitor.notifications.alert_escalator import AlertEscalator
from ai_project_health_monitor.notifications.alert_escalator_notifier import AlertEscalatorNotifier
from ai_project_health_monitor.notifications.alert_notifier import AlertNotifier
from ai_project_health_monitor.notifications.health_summary_notifier import (
    HealthSummaryNotifier,
)
from ai_project_health_monitor.orchestration.graph import (
    build_project_health_graph,
)
from ai_project_health_monitor.persistence.repositories.in_memory_health_snapshot import (
    InMemoryHealthSnapshotRepository,
)
from ai_project_health_monitor.rag.models.chunk import DocumentChunk
from ai_project_health_monitor.rag.models.retrieval import RetrievalResult
from ai_project_health_monitor.rag.project_health_retrieval import (
    ProjectHealthEvidenceRetriever,
)


def test_project_health_graph_executes_end_to_end() -> None:
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
    health_snapshot_repository = InMemoryHealthSnapshotRepository()

    chunk = DocumentChunk(
        chunk_id="CHUNK-001",
        project_id="PROJ-001",
        event_id="EVT-001",
        source_type=SourceType.JIRA,
        source_id="PROJ-101",
        content="Payment API integration is blocked.",
        chunk_index=0,
        occurred_at=datetime(
            2026,
            9,
            1,
            tzinfo=UTC,
        ),
    )

    retrieval_result = RetrievalResult(
        chunk=chunk,
        score=0.9,
    )

    risk_signal = RiskSignal(
        signal_id="SIG-001",
        project_id="PROJ-001",
        event_id="EVT-001",
        risk_type=RiskType.BLOCKER,
        severity=RiskSeverity.HIGH,
        confidence=0.95,
        evidence=Evidence(
            event_id="EVT-001",
            source_type=SourceType.JIRA,
            source_id="PROJ-101",
            content="Payment API integration is blocked.",
            occurred_at=datetime(
                2026,
                9,
                1,
                tzinfo=UTC,
            ),
        ),
        evidence_quote="Payment API integration is blocked.",
        rationale="Payment API integration is blocked.",
    )

    risk_group = RiskGroup(
        primary_risk=risk_signal,
    )

    health_score = HealthScore(
        project_id="PROJ-001",
        score=60.0,
        status=HealthStatus.AT_RISK,
        contributing_risks=["SIG-001"],
        calculated_at=datetime(
            2026,
            9,
            1,
            tzinfo=UTC,
        ),
        rationale="Project has significant delivery risks.",
    )

    summary = ProjectHealthSummary(
        project_id="PROJ-001",
        health_score=60.0,
        health_status=HealthStatus.AT_RISK,
        executive_summary="Project has significant delivery risks.",
        top_risks=[],
        recommended_actions=[],
    )

    alert = HealthAlert(
        project_id="PROJ-001",
        health_score=60.0,
        health_status=HealthStatus.AT_RISK,
        message="No critical alert required.",
        triggered=False,
    )

    retrieval_service.retrieve.return_value = [
        retrieval_result,
    ]

    risk_analyzer.analyze.return_value = [
        risk_signal,
    ]

    risk_consolidator.consolidate.return_value = [
        risk_group,
    ]

    risk_consolidator.primary_risks.return_value = [
        risk_signal,
    ]

    health_scorer.calculate.return_value = health_score

    summary_generator.generate.return_value = summary

    alert_evaluator.evaluate.return_value = alert

    graph = build_project_health_graph(
        evidence_retriever=retrieval_service,
        risk_analyzer=risk_analyzer,
        risk_consolidator=risk_consolidator,
        health_scorer=health_scorer,
        summary_generator=summary_generator,
        alert_evaluator=alert_evaluator,
        notifier=notifier,
        deduplicator=deduplicator,
        escalator=escalator,
        escalation_notifier=escalation_notifier,
        summary_notifier=summary_notifier,
        health_snapshot_repository=health_snapshot_repository,
    )

    result = graph.invoke(
        {
            "project_id": "PROJ-001",
            "query": "What risks are affecting the project?",
        }
    )

    snapshots = health_snapshot_repository.get_history("PROJ-001")

    assert len(snapshots) == 1
    assert snapshots[0].project_id == "PROJ-001"
    assert snapshots[0].health_score == health_score.score
    assert snapshots[0].health_status == health_score.status
    assert snapshots[0].risk_signals == [risk_signal]
    assert snapshots[0].calculated_at == health_score.calculated_at

    summary_notifier.notify.assert_called_once_with(summary)
    assert result["project_id"] == "PROJ-001"
    assert result["query"] == "What risks are affecting the project?"

    assert result["retrieval_results"] == [
        retrieval_result,
    ]

    assert len(result["evidence"]) == 1
    assert result["evidence"][0].event_id == "EVT-001"
    assert result["evidence"][0].source_type == SourceType.JIRA
    assert result["evidence"][0].source_id == "PROJ-101"

    assert result["risk_signals"] == [
        risk_signal,
    ]

    assert result["risk_groups"] == [
        risk_group,
    ]

    assert result["primary_risks"] == [
        risk_signal,
    ]

    assert result["health_score"] == health_score
    assert result["summary"] == summary
    assert result["alert"] == alert

    retrieval_service.retrieve.assert_called_once_with(
        project_id="PROJ-001",
    )

    risk_analyzer.analyze.assert_called_once_with(
        project_id="PROJ-001",
        query="What risks are affecting the project?",
        evidence=result["evidence"],
    )

    risk_consolidator.consolidate.assert_called_once_with(
        [risk_signal],
    )

    risk_consolidator.primary_risks.assert_called_once_with(
        [risk_group],
    )

    health_scorer.calculate.assert_called_once_with(
        project_id="PROJ-001",
        risk_signals=[risk_signal],
    )

    summary_generator.generate.assert_called_once_with(
        health_score=health_score,
        risk_signals=[risk_signal],
    )

    alert_evaluator.evaluate.assert_called_once_with(
        health_score=health_score,
    )

    notifier.notify.assert_not_called()


def test_project_health_graph_scores_only_primary_risks() -> None:
    retrieval_service = Mock(spec=ProjectHealthEvidenceRetriever)
    risk_analyzer = Mock(spec=LLMRiskAnalyzer)
    risk_consolidator = RiskConsolidator()
    health_scorer = DeterministicHealthScorer()
    summary_generator = Mock(spec=HealthSummaryGenerator)
    alert_evaluator = Mock(spec=HealthAlertEvaluator)
    notifier = Mock(spec=AlertNotifier)
    deduplicator = Mock(spec=AlertDeduplicator)
    escalator = Mock(spec=AlertEscalator)
    escalation_notifier = Mock(spec=AlertEscalatorNotifier)
    summary_notifier = Mock(spec=HealthSummaryNotifier)
    health_snapshot_repository = InMemoryHealthSnapshotRepository()

    evidence = Evidence(
        event_id="EVT-001",
        source_type=SourceType.JIRA,
        source_id="EVT-001",
        content=(
            "Payment API integration is blocked because "
            "the external API team has not provided credentials."
        ),
        occurred_at=datetime(
            2026,
            9,
            1,
            tzinfo=UTC,
        ),
    )

    blocker = RiskSignal(
        signal_id="SIG-001",
        project_id="PROJ-001",
        event_id="EVT-001",
        risk_type=RiskType.BLOCKER,
        severity=RiskSeverity.HIGH,
        confidence=0.9,
        evidence=evidence,
        evidence_quote=evidence.content,
        rationale="Payment API integration is blocked.",
    )

    dependency = RiskSignal(
        signal_id="SIG-002",
        project_id="PROJ-001",
        event_id="EVT-001",
        risk_type=RiskType.DEPENDENCY,
        severity=RiskSeverity.HIGH,
        confidence=0.9,
        evidence=evidence,
        evidence_quote=evidence.content,
        rationale="The external API team has not provided credentials.",
    )

    risk_analyzer.analyze.return_value = [
        blocker,
        dependency,
    ]

    retrieval_service.retrieve.return_value = []

    summary = ProjectHealthSummary(
        project_id="PROJ-001",
        health_score=82.0,
        health_status=HealthStatus.HEALTHY,
        executive_summary="Project health is healthy.",
        top_risks=[],
        recommended_actions=[],
    )

    alert = HealthAlert(
        project_id="PROJ-001",
        health_score=82.0,
        health_status=HealthStatus.HEALTHY,
        message="No critical alert required.",
        triggered=False,
    )

    summary_generator.generate.return_value = summary
    alert_evaluator.evaluate.return_value = alert

    graph = build_project_health_graph(
        evidence_retriever=retrieval_service,
        risk_analyzer=risk_analyzer,
        risk_consolidator=risk_consolidator,
        health_scorer=health_scorer,
        summary_generator=summary_generator,
        alert_evaluator=alert_evaluator,
        notifier=notifier,
        deduplicator=deduplicator,
        escalator=escalator,
        escalation_notifier=escalation_notifier,
        summary_notifier=summary_notifier,
        health_snapshot_repository = health_snapshot_repository
    )

    result = graph.invoke(
        {
            "project_id": "PROJ-001",
            "query": "What risks are affecting the payment API?",
        }
    )

    assert len(result["risk_signals"]) == 2
    assert len(result["risk_groups"]) == 1
    assert result["primary_risks"] == [blocker]

    health_score = result["health_score"]

    assert health_score.score == 82.0
    assert health_score.status == HealthStatus.HEALTHY
    assert health_score.contributing_risks == ["SIG-001"]

    assert result["summary"] == summary
    assert result["alert"] == alert

    summary_generator.generate.assert_called_once_with(
        health_score=health_score,
        risk_signals=[blocker],
    )

    alert_evaluator.evaluate.assert_called_once_with(
        health_score=health_score,
    )

    notifier.notify.assert_not_called()


def test_project_health_graph_triggers_alert_for_critical_health() -> None:
    retrieval_service = Mock(spec=ProjectHealthEvidenceRetriever)
    risk_analyzer = Mock(spec=LLMRiskAnalyzer)
    risk_consolidator = RiskConsolidator()
    health_scorer = DeterministicHealthScorer()
    summary_generator = Mock(spec=HealthSummaryGenerator)
    alert_evaluator = Mock(spec=HealthAlertEvaluator)
    notifier = Mock(spec=AlertNotifier)
    deduplicator = Mock(spec=AlertDeduplicator)
    escalator = Mock(spec=AlertEscalator)
    escalation_notifier = Mock(spec=AlertEscalatorNotifier)
    summary_notifier = Mock(spec=HealthSummaryNotifier)
    health_snapshot_repository = InMemoryHealthSnapshotRepository()

    evidence = Evidence(
        event_id="EVT-001",
        source_type=SourceType.JIRA,
        source_id="EVT-001",
        content="Production deployment is blocked by a critical issue.",
        occurred_at=datetime(
            2026,
            9,
            1,
            tzinfo=UTC,
        ),
    )

    risk_signal = RiskSignal(
        signal_id="SIG-001",
        project_id="PROJ-001",
        event_id="EVT-001",
        risk_type=RiskType.BLOCKER,
        severity=RiskSeverity.CRITICAL,
        confidence=1.0,
        evidence=evidence,
        evidence_quote=evidence.content,
        rationale="Production deployment is blocked.",
    )

    evidence_2 = Evidence(
        event_id="EVT-002",
        source_type=SourceType.JIRA,
        source_id="EVT-002",
        content="Critical delivery delay has put the release timeline at risk.",
        occurred_at=datetime(
            2026,
            9,
            2,
            tzinfo=UTC,
        ),
    )

    risk_signal_2 = RiskSignal(
        signal_id="SIG-002",
        project_id="PROJ-001",
        event_id="EVT-002",
        risk_type=RiskType.DELAY,
        severity=RiskSeverity.CRITICAL,
        confidence=1.0,
        evidence=evidence_2,
        evidence_quote=evidence_2.content,
        rationale="Critical delivery delay detected.",
    )

    alert = HealthAlert(
        project_id="PROJ-001",
        health_score=30.0,
        health_status=HealthStatus.CRITICAL,
        message="Immediate attention is required.",
        triggered=True,
    )

    retrieval_service.retrieve.return_value = []
    risk_analyzer.analyze.return_value = [
        risk_signal,
        risk_signal_2,
    ]

    summary = ProjectHealthSummary(
    project_id="PROJ-001",
    health_score=30.0,
    health_status=HealthStatus.CRITICAL,
    executive_summary="Project health is critical.",
    top_risks=[],
    recommended_actions=[
        "Resolve the production deployment blocker.",
    ],
)

    summary_generator.generate.return_value = summary

    alert_evaluator.evaluate.return_value = alert

    graph = build_project_health_graph(
        evidence_retriever=retrieval_service,
        risk_analyzer=risk_analyzer,
        risk_consolidator=risk_consolidator,
        health_scorer=health_scorer,
        summary_generator=summary_generator,
        alert_evaluator=alert_evaluator,
        notifier=notifier,
        deduplicator=deduplicator,
        escalator=escalator,
        escalation_notifier=escalation_notifier,
        summary_notifier=summary_notifier,
        health_snapshot_repository=health_snapshot_repository,
    )

    result = graph.invoke(
        {
            "project_id": "PROJ-001",
            "query": "What is the current project health?",
        }
    )
    summary_notifier.notify.assert_called_once_with(summary)
    assert result["health_score"].score == 30.0
    assert result["health_score"].status == HealthStatus.CRITICAL
    assert result["alert"] == alert
    assert result["alert_triggered"] is True

    alert_evaluator.evaluate.assert_called_once_with(
        health_score=result["health_score"],
    )

    notifier.notify.assert_called_once_with(alert)