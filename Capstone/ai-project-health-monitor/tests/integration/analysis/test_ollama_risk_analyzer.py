from datetime import UTC, datetime

from ai_project_health_monitor.analysis.llm_risk_analyzer import LLMRiskAnalyzer
from ai_project_health_monitor.analysis.ollama import OllamaLLMClient
from ai_project_health_monitor.analysis.risk_grounding_validator import (
    DeterministicRiskGroundingValidator,
)
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.project_event import SourceType


def test_qwen3_extracts_risk_from_project_evidence() -> None:
    llm_client = OllamaLLMClient(
        model="qwen3:8b",
    )

    analyzer = LLMRiskAnalyzer(
        llm_client=llm_client,
        grounding_validator=DeterministicRiskGroundingValidator(),
    )

    evidence = [
        Evidence(
            event_id="EVT-JIRA-001",
            source_type=SourceType.JIRA,
            source_id="EVT-JIRA-001",
            content=(
                "Payment API integration is currently blocked "
                "because the external API team has not provided "
                "the required credentials."
            ),
            occurred_at=datetime(
                2026,
                9,
                1,
                tzinfo=UTC,
            ),
        )
    ]

    signals = analyzer.analyze(
        project_id="PROJ-001",
        query="What risks are affecting the payment API integration?",
        evidence=evidence,
    )

    assert signals

    signal = signals[0]

    assert signal.project_id == "PROJ-001"
    assert signal.evidence.source_id == "EVT-JIRA-001"
    assert signal.rationale
    assert 0.0 <= signal.confidence <= 1.0