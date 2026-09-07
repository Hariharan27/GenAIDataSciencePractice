from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from ai_project_health_monitor.analysis.health_scorer import HealthScorer
from ai_project_health_monitor.analysis.llm import LLMClient
from ai_project_health_monitor.analysis.llm_risk_analyzer import LLMRiskAnalyzer
from ai_project_health_monitor.analysis.project_health import ProjectHealthService
from ai_project_health_monitor.analysis.risk_analyzer import RiskAnalyzer
from ai_project_health_monitor.analysis.risk_consolidator import RiskConsolidator
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.health_score import HealthScore, HealthStatus
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)
from ai_project_health_monitor.rag.models.chunk import DocumentChunk
from ai_project_health_monitor.rag.models.retrieval import RetrievalResult


@pytest.fixture
def llm_client() -> Mock:
    return Mock(spec=LLMClient)


@pytest.fixture
def evidence() -> list[Evidence]:
    return [
        Evidence(
            event_id="EVT-JIRA-001",
            source_type=SourceType.JIRA,
            source_id="EVT-JIRA-001",
            content=(
                "Payment API integration is blocked because "
                "external API credentials are missing."
            ),
            occurred_at=datetime(
                2026,
                9,
                1,
                tzinfo=UTC,
            ),
        )
    ]


@pytest.fixture
def query() -> str:
    return "What risks are affecting the payment API integration?"


def test_analyze_extracts_valid_risk_signal(
    llm_client: Mock,
    evidence: list[Evidence],
    query: str,
) -> None:
    llm_client.generate.return_value = """
    [
        {
            "risk_type": "blocker",
            "severity": "high",
            "confidence": 0.95,
            "evidence_source_id": "EVT-JIRA-001",
            "evidence_quote": "Payment API integration is blocked because external API credentials are missing.",
            "rationale": "The payment API integration is blocked by missing credentials."
        }
    ]
    """

    analyzer = LLMRiskAnalyzer(llm_client)

    signals = analyzer.analyze(
        project_id="PROJ-001",
        query=query,
        evidence=evidence,
    )

    assert len(signals) == 1

    signal = signals[0]

    assert signal.project_id == "PROJ-001"
    assert signal.risk_type == RiskType.BLOCKER
    assert signal.severity == RiskSeverity.HIGH
    assert signal.confidence == 0.95
    assert signal.event_id == "EVT-JIRA-001"
    assert signal.evidence.source_id == "EVT-JIRA-001"
    assert "blocked" in signal.rationale.lower()


def test_analyze_returns_empty_list_when_no_risk(
    llm_client: Mock,
    evidence: list[Evidence],
    query: str,
) -> None:
    llm_client.generate.return_value = "[]"

    analyzer = LLMRiskAnalyzer(llm_client)

    signals = analyzer.analyze(
        project_id="PROJ-001",
        query=query,
        evidence=evidence,
    )

    assert signals == []


def test_analyze_rejects_invalid_json(
    llm_client: Mock,
    evidence: list[Evidence],
    query: str,
) -> None:
    llm_client.generate.return_value = "This is not JSON."

    analyzer = LLMRiskAnalyzer(llm_client)

    with pytest.raises(
        ValueError,
        match="LLM response must contain valid JSON",
    ):
        analyzer.analyze(
            project_id="PROJ-001",
            query=query,
            evidence=evidence,
        )


def test_analyze_rejects_non_array_response(
    llm_client: Mock,
    evidence: list[Evidence],
    query: str,
) -> None:
    llm_client.generate.return_value = """
    {
        "risk_type": "blocker"
    }
    """

    analyzer = LLMRiskAnalyzer(llm_client)

    with pytest.raises(
        ValueError,
        match="LLM response must be a JSON array",
    ):
        analyzer.analyze(
            project_id="PROJ-001",
            query=query,
            evidence=evidence,
        )


def test_analyze_rejects_unknown_evidence_reference(
    llm_client: Mock,
    evidence: list[Evidence],
    query: str,
) -> None:
    llm_client.generate.return_value = """
    [
        {
            "risk_type": "blocker",
            "severity": "high",
            "confidence": 0.95,
            "evidence_source_id": "EVT-UNKNOWN",
            "evidence_quote": "The project is blocked.",
            "rationale": "The project is blocked."
        }
    ]
    """

    analyzer = LLMRiskAnalyzer(llm_client)

    with pytest.raises(
        ValueError,
        match="LLM referenced evidence that was not provided",
    ):
        analyzer.analyze(
            project_id="PROJ-001",
            query=query,
            evidence=evidence,
        )


def test_analyze_rejects_invalid_confidence(
    llm_client: Mock,
    evidence: list[Evidence],
    query: str,
) -> None:
    llm_client.generate.return_value = """
    [
        {
            "risk_type": "blocker",
            "severity": "high",
            "confidence": 1.5,
            "evidence_source_id": "EVT-JIRA-001",
            "rationale": "The project is blocked."
        }
    ]
    """

    analyzer = LLMRiskAnalyzer(llm_client)

    with pytest.raises(ValueError):
        analyzer.analyze(
            project_id="PROJ-001",
            query=query,
            evidence=evidence,
        )


def test_analyze_returns_empty_for_empty_evidence(
    llm_client: Mock,
    query: str,
) -> None:
    analyzer = LLMRiskAnalyzer(llm_client)

    signals = analyzer.analyze(
        project_id="PROJ-001",
        query=query,
        evidence=[],
    )

    assert signals == []
    llm_client.generate.assert_not_called()


def test_analyze_rejects_empty_project_id(
    llm_client: Mock,
    evidence: list[Evidence],
    query: str,
) -> None:
    analyzer = LLMRiskAnalyzer(llm_client)

    with pytest.raises(
        ValueError,
        match="project_id cannot be empty",
    ):
        analyzer.analyze(
            project_id="   ",
            query=query,
            evidence=evidence,
        )


def test_analyze_rejects_empty_query(
    llm_client: Mock,
    evidence: list[Evidence],
) -> None:
    analyzer = LLMRiskAnalyzer(llm_client)

    with pytest.raises(
        ValueError,
        match="query cannot be empty",
    ):
        analyzer.analyze(
            project_id="PROJ-001",
            query="   ",
            evidence=evidence,
        )

def test_analyze_scores_only_primary_risk_after_consolidation() -> None:
        risk_analyzer = Mock(spec=RiskAnalyzer)
        health_scorer = Mock(spec=HealthScorer)
        risk_consolidator = RiskConsolidator()

        evidence = Evidence(
            event_id="EVT-001",
            source_type=SourceType.JIRA,
            source_id="EVT-001",
            content="Payment API is blocked by missing credentials.",
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
            rationale="Payment API is blocked.",
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
            rationale="External credentials are missing.",
        )

        delay = RiskSignal(
            signal_id="SIG-003",
            project_id="PROJ-001",
            event_id="EVT-001",
            risk_type=RiskType.DELAY,
            severity=RiskSeverity.HIGH,
            confidence=0.9,
            evidence=evidence,
            evidence_quote=evidence.content,
            rationale="Release may be delayed.",
        )

        risk_analyzer.analyze.return_value = [
            blocker,
            dependency,
            delay,
        ]

        expected_health_score = HealthScore(
            project_id="PROJ-001",
            score=80.0,
            status=HealthStatus.AT_RISK,
            contributing_risks=["SIG-001"],
            calculated_at=datetime(
                2026,
                9,
                1,
                tzinfo=UTC,
            ),
            rationale="Test health score.",
        )

        health_scorer.calculate.return_value = expected_health_score

        service = ProjectHealthService(
            risk_analyzer=risk_analyzer,
            health_scorer=health_scorer,
            risk_consolidator=risk_consolidator,
        )

        retrieval_result = RetrievalResult(
            chunk=DocumentChunk(
                chunk_id="CHUNK-001",
                project_id="PROJ-001",
                event_id="EVT-001",
                source_type=SourceType.JIRA,
                source_id="EVT-001",
                content=evidence.content,
                chunk_index=0,
                occurred_at=evidence.occurred_at,
            ),
            score=0.9,
        )

        result = service.analyze(
            project_id="PROJ-001",
            query="What are the payment API risks?",
            retrieval_results=[retrieval_result],
        )

        assert result == expected_health_score

        health_scorer.calculate.assert_called_once()

        scored_risks = health_scorer.calculate.call_args.kwargs["risk_signals"]

        assert len(scored_risks) == 2

        assert [
            signal.risk_type
            for signal in scored_risks
        ] == [
            RiskType.BLOCKER,
            RiskType.DELAY,
        ]

        assert [
            signal.signal_id
            for signal in scored_risks
        ] == [
            "SIG-001",
            "SIG-003",
        ]