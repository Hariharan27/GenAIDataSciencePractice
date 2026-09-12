from datetime import UTC, datetime

from ai_project_health_monitor.analysis.llm_risk_change_investigator import (
    LLMRiskChangeInvestigator,
)
from ai_project_health_monitor.analysis.ollama import OllamaLLMClient
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.risk_change import RiskChangeType
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)
from ai_project_health_monitor.domain.models.project_event import SourceType


def test_qwen3_investigates_continuing_project_risk() -> None:
    llm_client = OllamaLLMClient(
        model="qwen3:8b",
    )

    investigator = LLMRiskChangeInvestigator(
        llm_client=llm_client,
    )

    previous_evidence = Evidence(
        event_id="EVT-JIRA-001",
        source_type=SourceType.JIRA,
        source_id="EVT-JIRA-001",
        content=(
            "Payment API integration is blocked because the "
            "external API team has not provided the required "
            "credentials."
        ),
        occurred_at=datetime(
            2026,
            9,
            1,
            tzinfo=UTC,
        ),
    )

    current_evidence = Evidence(
        event_id="EVT-JIRA-002",
        source_type=SourceType.JIRA,
        source_id="EVT-JIRA-002",
        content=(
            "Payment API integration remains blocked. "
            "The external API team still has not provided "
            "the required credentials."
        ),
        occurred_at=datetime(
            2026,
            9,
            2,
            tzinfo=UTC,
        ),
    )

    previous_risk = RiskSignal(
        signal_id="SIG-001",
        project_id="PROJ-001",
        event_id="EVT-JIRA-001",
        risk_type=RiskType.BLOCKER,
        severity=RiskSeverity.HIGH,
        confidence=0.95,
        evidence=previous_evidence,
        evidence_quote=(
            "Payment API integration is blocked because the "
            "external API team has not provided the required "
            "credentials."
        ),
        rationale="Required external credentials are unavailable.",
    )

    current_risk = RiskSignal(
        signal_id="SIG-002",
        project_id="PROJ-001",
        event_id="EVT-JIRA-002",
        risk_type=RiskType.BLOCKER,
        severity=RiskSeverity.HIGH,
        confidence=0.96,
        evidence=current_evidence,
        evidence_quote=(
            "Payment API integration remains blocked. "
            "The external API team still has not provided "
            "the required credentials."
        ),
        rationale="The same external credential blocker remains unresolved.",
    )

    changes = investigator.investigate(
        project_id="PROJ-001",
        previous_risks=[previous_risk],
        current_risks=[current_risk],
        evidence=[current_evidence],
    )

    assert changes

    change = changes[0]

    assert change.project_id == "PROJ-001"
    assert change.change_type == RiskChangeType.CONTINUING
    assert change.previous_risk is not None
    assert change.previous_risk.signal_id == "SIG-001"
    assert change.current_risk is not None
    assert change.current_risk.signal_id == "SIG-002"
    assert change.rationale