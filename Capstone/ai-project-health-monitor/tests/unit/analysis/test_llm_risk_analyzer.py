import json
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from ai_project_health_monitor.analysis.llm import LLMClient
from ai_project_health_monitor.analysis.llm_risk_analyzer import LLMRiskAnalyzer
from ai_project_health_monitor.analysis.risk_grounding_validator import (
    DeterministicRiskGroundingValidator,
    RiskGroundingValidator,
)
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
def grounding_validator() -> RiskGroundingValidator:
    return DeterministicRiskGroundingValidator()


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
    grounding_validator: RiskGroundingValidator,
    evidence: list[Evidence],
    query: str,
) -> None:

    llm_client.generate.return_value = json.dumps(
        [
                {
                    "risk_type": "blocker",
                    "severity": "high",
                    "confidence": 0.95,
                    "evidence_source_id": "EVT-JIRA-001",
                    "evidence_quote": (
                        "Payment API integration is blocked because external API "
                        "credentials are missing."
                     ),
                    "rationale": "The payment API integration is blocked by missing credentials."
                }
            ]
    )

    analyzer = LLMRiskAnalyzer(
        llm_client,
        grounding_validator,
    )

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
    grounding_validator: RiskGroundingValidator,
    evidence: list[Evidence],
    query: str,
) -> None:
    llm_client.generate.return_value = "[]"

    analyzer = LLMRiskAnalyzer(
        llm_client,
        grounding_validator,
    )

    signals = analyzer.analyze(
        project_id="PROJ-001",
        query=query,
        evidence=evidence,
    )

    assert signals == []


def test_analyze_rejects_invalid_json(
    llm_client: Mock,
    grounding_validator: RiskGroundingValidator,
    evidence: list[Evidence],
    query: str,
) -> None:
    llm_client.generate.return_value = "This is not JSON."

    analyzer = LLMRiskAnalyzer(
        llm_client,
        grounding_validator,
    )

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
    grounding_validator: RiskGroundingValidator,
    evidence: list[Evidence],
    query: str,
) -> None:
    llm_client.generate.return_value = """
    {
        "risk_type": "blocker"
    }
    """

    analyzer = LLMRiskAnalyzer(
        llm_client,
        grounding_validator,
    )

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
    grounding_validator: RiskGroundingValidator,
    evidence: list[Evidence],
    query: str,
) -> None:

    llm_client.generate.return_value = json.dumps(
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
    )

    analyzer = LLMRiskAnalyzer(
        llm_client,
        grounding_validator,
    )

    signals = analyzer.analyze(
        project_id="PROJ-001",
        query=query,
        evidence=evidence,
    )

    assert signals == []


def test_analyze_rejects_invalid_confidence(
    llm_client: Mock,
    grounding_validator: RiskGroundingValidator,
    evidence: list[Evidence],
    query: str,
) -> None:

    llm_client.generate.return_value = json.dumps(
        [
                {
                    "risk_type": "blocker",
                    "severity": "high",
                    "confidence": 1.5,
                    "evidence_source_id": "EVT-JIRA-001",
                    "evidence_quote": (
                        "Payment API integration is blocked because external API "
                        "credentials are missing."
                    ),
                    "rationale": "The project is blocked."
                }
            ]
    )

    analyzer = LLMRiskAnalyzer(
        llm_client,
        grounding_validator,
    )

    signals = analyzer.analyze(
        project_id="PROJ-001",
        query=query,
        evidence=evidence,
    )

    assert signals == []


def test_analyze_returns_empty_for_empty_evidence(
    llm_client: Mock,
    grounding_validator: RiskGroundingValidator,
    query: str,
) -> None:
    analyzer = LLMRiskAnalyzer(
        llm_client,
        grounding_validator,
    )

    signals = analyzer.analyze(
        project_id="PROJ-001",
        query=query,
        evidence=[],
    )

    assert signals == []
    llm_client.generate.assert_not_called()


def test_analyze_rejects_empty_project_id(
    llm_client: Mock,
    grounding_validator: RiskGroundingValidator,
    evidence: list[Evidence],
    query: str,
) -> None:
    analyzer = LLMRiskAnalyzer(
        llm_client,
        grounding_validator,
    )

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
    grounding_validator: RiskGroundingValidator,
    evidence: list[Evidence],
) -> None:
    analyzer = LLMRiskAnalyzer(
        llm_client,
        grounding_validator,
    )

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
    analyzer = LLMRiskAnalyzer(
        Mock(spec=LLMClient),
        DeterministicRiskGroundingValidator(),
    )

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
    assert "impact or consequence" in prompt
    assert "affecting the planned release date" in prompt
    assert "Do NOT use DELIVERY as a synonym for DELAY." in prompt


def test_prompt_lists_valid_evidence_source_ids() -> None:
    evidence = [
        Evidence(
            event_id="EVT-001",
            source_type=SourceType.JIRA,
            source_id="JIRA-001",
            content="Payment API integration is blocked.",
            occurred_at=datetime(
                2026,
                9,
                1,
                tzinfo=UTC,
            ),
        ),
        Evidence(
            event_id="EVT-002",
            source_type=SourceType.EMAIL,
            source_id="EMAIL-001",
            content="The release date is affected.",
            occurred_at=datetime(
                2026,
                9,
                1,
                tzinfo=UTC,
            ),
        ),
    ]

    prompt = LLMRiskAnalyzer._build_prompt(
        project_id="PROJ-001",
        query="What risks affect the payment integration?",
        evidence=evidence,
    )

    assert "VALID EVIDENCE SOURCE IDS" in prompt
    assert "- JIRA-001" in prompt
    assert "- EMAIL-001" in prompt


def test_prompt_distinguishes_delay_from_delivery() -> None:
    evidence = [
        Evidence(
            event_id="EVT-001",
            source_type=SourceType.JIRA,
            source_id="JIRA-001",
            content="Backend development is three days behind schedule.",
            occurred_at=datetime(
                2026,
                9,
                1,
                tzinfo=UTC,
            ),
        )
    ]

    prompt = LLMRiskAnalyzer._build_prompt(
        project_id="PROJ-001",
        query="What risks affect the backend?",
        evidence=evidence,
    )

    assert "Do NOT use DELIVERY as a synonym for DELAY." in prompt
    assert "Report DELAY only when the evidence explicitly states" in prompt


def test_parse_response_rejects_unknown_evidence_source_id() -> None:
    evidence = [
        Evidence(
            event_id="EVT-001",
            source_type=SourceType.JIRA,
            source_id="JIRA-001",
            content="Payment API integration is blocked.",
            occurred_at=datetime(
                2026,
                9,
                1,
                tzinfo=UTC,
            ),
        )
    ]

    response = """
    [
        {
            "risk_type": "blocker",
            "severity": "high",
            "confidence": 0.95,
            "evidence_source_id": "HALLUCINATED-001",
            "evidence_quote": "Unsupported risk.",
            "rationale": "Unsupported risk."
        }
    ]
    """

    analyzer = LLMRiskAnalyzer(
        Mock(spec=LLMClient),
        DeterministicRiskGroundingValidator(),
    )

    signals = analyzer._parse_response(
        project_id="PROJ-001",
        evidence=evidence,
        response=response,
    )

    assert signals == []


def test_parse_response_accepts_empty_array() -> None:
    analyzer = LLMRiskAnalyzer(
        Mock(spec=LLMClient),
        DeterministicRiskGroundingValidator(),
    )

    signals = analyzer._parse_response(
        project_id="PROJ-002",
        evidence=[],
        response="[]",
    )

    assert signals == []


def test_build_prompt_requires_exact_evidence_source_id() -> None:
    analyzer = LLMRiskAnalyzer(
        Mock(spec=LLMClient),
        DeterministicRiskGroundingValidator(),
    )

    evidence = [
        Evidence(
            event_id="EVT-001",
            source_type=SourceType.JIRA,
            source_id="JIRA-001",
            content="Payment API integration is blocked.",
            occurred_at=datetime(
                2026,
                9,
                1,
                tzinfo=UTC,
            ),
        )
    ]

    prompt = analyzer._build_prompt(
        project_id="PROJ-001",
        query="What risks affect the payment integration?",
        evidence=evidence,
    )

    assert "MUST be copied EXACTLY" in prompt
    assert "NEVER invent, modify, abbreviate, or guess" in prompt
    assert "- JIRA-001" in prompt


def test_build_prompt_requires_empty_array_when_no_supported_risk() -> None:
    analyzer = LLMRiskAnalyzer(
        Mock(spec=LLMClient),
        DeterministicRiskGroundingValidator(),
    )

    evidence = [
        Evidence(
            event_id="EVT-001",
            source_type=SourceType.JIRA,
            source_id="JIRA-001",
            content="Reporting module completed successfully.",
            occurred_at=datetime(
                2026,
                9,
                1,
                tzinfo=UTC,
            ),
        )
    ]

    prompt = analyzer._build_prompt(
        project_id="PROJ-002",
        query="Are there any risks affecting the reporting project?",
        evidence=evidence,
    )

    assert "Positive evidence does not constitute a risk." in prompt
    assert "If no provided evidence supports a relevant risk, return:" in prompt
    assert "FINAL EVIDENCE VERIFICATION" in prompt


def test_analyze_rejects_cross_project_evidence_reference(
    llm_client: Mock,
    grounding_validator: RiskGroundingValidator,
    evidence: list[Evidence],
    query: str,
) -> None:

    llm_client.generate.return_value = json.dumps(
        [
                {
                    "risk_type": "blocker",
                    "severity": "high",
                    "confidence": 0.95,
                    "evidence_source_id": "EVT-JIRA-999",
                    "evidence_quote": "Payment API integration is blocked.",
                    "rationale": "The payment API integration is blocked."
                }
        ]
    )

    analyzer = LLMRiskAnalyzer(
        llm_client,
        grounding_validator,
    )

    signals = analyzer.analyze(
        project_id="PROJ-002",
        query=query,
        evidence=evidence,
    )

    assert signals == []