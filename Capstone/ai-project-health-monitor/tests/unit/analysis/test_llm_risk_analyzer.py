from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from ai_project_health_monitor.analysis.llm import LLMClient
from ai_project_health_monitor.analysis.llm_risk_analyzer import LLMRiskAnalyzer
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskType,
)


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
def test_build_prompt_allows_explicit_downstream_risk() -> None:
    analyzer = LLMRiskAnalyzer(Mock(spec=LLMClient))

    evidence = Evidence(
        event_id="EVT-001",
        source_type=SourceType.JIRA,
        source_id="EVT-001",
        content=(
            "Payment API integration is blocked and "
            "this is affecting the planned release date."
        ),
        occurred_at=datetime(
            2026,
            9,
            1,
            tzinfo=UTC,
        ),
    )

    prompt = analyzer._build_prompt(
        project_id="PROJ-001",
        query="What risks are affecting the payment API integration?",
        evidence=[evidence],
    )

    assert "downstream risk is valid" in prompt
    assert "affecting the planned release date" in prompt