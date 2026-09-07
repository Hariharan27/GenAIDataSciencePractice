from datetime import UTC, datetime
from unittest.mock import Mock

from ai_project_health_monitor.analysis.llm_risk_analyzer import LLMRiskAnalyzer
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)
from ai_project_health_monitor.orchestration.nodes.analyze_risks import (
    AnalyzeRisksNode,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.rag.models.retrieval import RetrievalResult


def test_analyze_risks_node_extracts_evidence_and_risks() -> None:
    risk_analyzer = Mock(spec=LLMRiskAnalyzer)

    retrieval_result = Mock(spec=RetrievalResult)

    retrieval_result.chunk = Mock()
    retrieval_result.chunk.event_id = "EVT-001"
    retrieval_result.chunk.source_type = SourceType.JIRA
    retrieval_result.chunk.source_id = "PROJ-101"
    retrieval_result.chunk.content = "Payment API integration is blocked."
    retrieval_result.chunk.occurred_at = datetime(
        2026,
        9,
        1,
        tzinfo=UTC,
    )

    expected_risk = RiskSignal(
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
        rationale="Payment API integration is blocked.",
    )

    risk_analyzer.analyze.return_value = [expected_risk]

    node = AnalyzeRisksNode(
        risk_analyzer=risk_analyzer,
    )

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What risks are affecting the payment API integration?",
        retrieval_results=[retrieval_result],
    )

    result = node(state)

    assert result["risk_signals"] == [expected_risk]

    evidence = result["evidence"]

    assert isinstance(evidence, list)
    assert len(evidence) == 1
    assert evidence[0].event_id == "EVT-001"
    assert evidence[0].source_id == "PROJ-101"

    risk_analyzer.analyze.assert_called_once()

    call = risk_analyzer.analyze.call_args

    assert call.kwargs["project_id"] == "PROJ-001"
    assert (
        call.kwargs["query"]
        == "What risks are affecting the payment API integration?"
    )
    assert call.kwargs["evidence"] == evidence