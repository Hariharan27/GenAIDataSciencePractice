from datetime import UTC, datetime
from unittest.mock import Mock

from ai_project_health_monitor.analysis.health_scorer import HealthScorer
from ai_project_health_monitor.analysis.llm_risk_analyzer import LLMRiskAnalyzer
from ai_project_health_monitor.analysis.risk_consolidator import RiskConsolidator
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.health_score import (
    HealthScore,
    HealthStatus,
)
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.risk_group import RiskGroup
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)
from ai_project_health_monitor.orchestration.graph import (
    build_project_health_graph,
)
from ai_project_health_monitor.rag.models.chunk import DocumentChunk
from ai_project_health_monitor.rag.models.retrieval import RetrievalResult
from ai_project_health_monitor.rag.retrieval import RetrievalService


def test_project_health_graph_executes_end_to_end() -> None:
    retrieval_service = Mock(spec=RetrievalService)
    risk_analyzer = Mock(spec=LLMRiskAnalyzer)
    risk_consolidator = Mock(spec=RiskConsolidator)
    health_scorer = Mock(spec=HealthScorer)

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

    graph = build_project_health_graph(
        retrieval_service=retrieval_service,
        risk_analyzer=risk_analyzer,
        risk_consolidator=risk_consolidator,
        health_scorer=health_scorer,
    )

    result = graph.invoke(
        {
            "project_id": "PROJ-001",
            "query": "What risks are affecting the project?",
        }
    )

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

    retrieval_service.retrieve.assert_called_once_with(
        query="What risks are affecting the project?",
        project_id="PROJ-001",
        limit=5,
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