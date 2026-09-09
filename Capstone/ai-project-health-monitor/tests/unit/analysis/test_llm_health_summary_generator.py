import json
from unittest.mock import Mock

import pytest

from ai_project_health_monitor.analysis.llm import LLMClient
from ai_project_health_monitor.analysis.llm_health_summary_generator import (
    LLMHealthSummaryGenerator,
)
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.health_score import (
    HealthScore,
    HealthStatus,
)
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)


def build_health_score() -> HealthScore:
    return HealthScore(
        project_id="PROJ-001",
        score=62.0,
        status=HealthStatus.AT_RISK,
        contributing_risks=["SIG-001"],
        calculated_at=__import__("datetime").datetime.now(
            __import__("datetime").UTC
        ),
        rationale="Project is at risk.",
    )


def build_risk_signal() -> RiskSignal:
    evidence = Evidence(
        event_id="EVT-001",
        source_type=SourceType.JIRA,
        source_id="EVT-001",
        content="Payment API integration is blocked.",
        occurred_at=__import__("datetime").datetime.now(
            __import__("datetime").UTC
        ),
    )

    return RiskSignal(
        signal_id="SIG-001",
        project_id="PROJ-001",
        event_id="EVT-001",
        risk_type=RiskType.BLOCKER,
        severity=RiskSeverity.HIGH,
        confidence=0.95,
        evidence=evidence,
        evidence_quote=evidence.content,
        rationale="Payment API integration is blocked.",
    )


def test_generate_preserves_authoritative_health_facts() -> None:
    llm_client = Mock(spec=LLMClient)
    llm_client.generate.return_value = json.dumps(
        {
            "executive_summary": "The project is currently at risk.",
            "top_risks": [
                {
                    "signal_id": "SIG-001",
                    "risk_type": "blocker",
                    "severity": "high",
                    "rationale": "The payment API is blocked.",
                }
            ],
            "recommended_actions": [
                "Resolve the external API dependency.",
            ],
        }
    )

    generator = LLMHealthSummaryGenerator(llm_client)

    result = generator.generate(
        health_score=build_health_score(),
        risk_signals=[build_risk_signal()],
    )

    assert result.project_id == "PROJ-001"
    assert result.health_score == 62.0
    assert result.health_status == HealthStatus.AT_RISK
    assert result.top_risks[0].signal_id == "SIG-001"


def test_generate_rejects_unknown_risk_reference() -> None:
    llm_client = Mock(spec=LLMClient)
    llm_client.generate.return_value = json.dumps(
        {
            "executive_summary": "The project is at risk.",
            "top_risks": [
                {
                    "signal_id": "SIG-999",
                    "risk_type": "blocker",
                    "severity": "high",
                    "rationale": "Unknown risk.",
                }
            ],
            "recommended_actions": [],
        }
    )

    generator = LLMHealthSummaryGenerator(llm_client)

    with pytest.raises(
        ValueError,
        match="SIG-999",
    ):
        generator.generate(
            health_score=build_health_score(),
            risk_signals=[build_risk_signal()],
        )


def test_generate_supports_no_risks() -> None:
    llm_client = Mock(spec=LLMClient)
    llm_client.generate.return_value = json.dumps(
        {
            "executive_summary": "The project is healthy.",
            "top_risks": [],
            "recommended_actions": [],
        }
    )

    health_score = HealthScore(
        project_id="PROJ-001",
        score=100.0,
        status=HealthStatus.HEALTHY,
        contributing_risks=[],
        calculated_at=build_health_score().calculated_at,
        rationale="No detected risks.",
    )

    generator = LLMHealthSummaryGenerator(llm_client)

    result = generator.generate(
        health_score=health_score,
        risk_signals=[],
    )

    assert result.health_score == 100.0
    assert result.health_status == HealthStatus.HEALTHY
    assert result.top_risks == []