import json

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from ai_project_health_monitor.analysis.llm import LLMClient
from ai_project_health_monitor.analysis.llm_risk_change_investigator import (
    LLMRiskChangeInvestigator,
)
from ai_project_health_monitor.analysis.risk_change_investigator import (
    RiskChangeInvestigator,
)
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.risk_change import RiskChangeType
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)


@pytest.fixture
def llm_client() -> Mock:
    return Mock(spec=LLMClient)


@pytest.fixture
def previous_risk() -> RiskSignal:
    return RiskSignal(
        signal_id="RISK-PREV-001",
        project_id="PROJ-001",
        event_id="EVT-PREV-001",
        risk_type=RiskType.BLOCKER,
        severity=RiskSeverity.HIGH,
        confidence=0.95,
        evidence=Evidence(
            event_id="EVT-PREV-001",
            source_type=SourceType.JIRA,
            source_id="JIRA-001",
            content=(
                "Payment API integration is blocked because "
                "external API credentials are missing."
            ),
            occurred_at=datetime(2026, 9, 1, tzinfo=UTC),
        ),
        evidence_quote=(
            "Payment API integration is blocked because "
            "external API credentials are missing."
        ),
        rationale="The integration cannot proceed without credentials.",
    )


@pytest.fixture
def current_risk() -> RiskSignal:
    return RiskSignal(
        signal_id="RISK-CURRENT-001",
        project_id="PROJ-001",
        event_id="EVT-CURRENT-001",
        risk_type=RiskType.BLOCKER,
        severity=RiskSeverity.HIGH,
        confidence=0.94,
        evidence=Evidence(
            event_id="EVT-CURRENT-001",
            source_type=SourceType.JIRA,
            source_id="JIRA-002",
            content=(
                "Payment API integration is still waiting for "
                "external API credentials."
            ),
            occurred_at=datetime(2026, 9, 10, tzinfo=UTC),
        ),
        evidence_quote=(
            "Payment API integration is still waiting for "
            "external API credentials."
        ),
        rationale="The integration is still waiting for credentials.",
    )


@pytest.fixture
def evidence() -> list[Evidence]:
    return [
        Evidence(
            event_id="EVT-CURRENT-001",
            source_type=SourceType.JIRA,
            source_id="JIRA-002",
            content=(
                "Payment API integration is still waiting for "
                "external API credentials."
            ),
            occurred_at=datetime(2026, 9, 10, tzinfo=UTC),
        )
    ]


def test_implements_risk_change_investigator(
    llm_client: Mock,
) -> None:
    investigator = LLMRiskChangeInvestigator(llm_client)

    assert isinstance(investigator, RiskChangeInvestigator)


def test_investigate_identifies_continuing_risk(
    llm_client: Mock,
    previous_risk: RiskSignal,
    current_risk: RiskSignal,
    evidence: list[Evidence],
) -> None:
    llm_client.generate.return_value = json.dumps(
        [
            {
                "change_type": "continuing",
                "previous_risk_signal_id": "RISK-PREV-001",
                "current_risk_signal_id": "RISK-CURRENT-001",
                "evidence_source_id": "JIRA-002",
                "rationale": (
                    "The payment API credential issue remains unresolved "
                    "in the latest project update."
                ),
            }
        ]
    )

    investigator = LLMRiskChangeInvestigator(llm_client)

    changes = investigator.investigate(
        project_id="PROJ-001",
        previous_risks=[previous_risk],
        current_risks=[current_risk],
        evidence=evidence,
    )

    assert len(changes) == 1
    change = changes[0]

    assert change.project_id == "PROJ-001"
    assert change.change_type == RiskChangeType.CONTINUING
    assert change.previous_risk == previous_risk
    assert change.current_risk == current_risk
    assert "remains unresolved" in change.rationale


def test_investigate_identifies_new_risk(
    llm_client: Mock,
    current_risk: RiskSignal,
    evidence: list[Evidence],
) -> None:
    llm_client.generate.return_value = json.dumps(
        [
            {
                "change_type": "new",
                "previous_risk_signal_id": None,
                "current_risk_signal_id": "RISK-CURRENT-001",
                "evidence_source_id": "JIRA-002",
                "rationale": "The issue is newly reported in the current state.",
            }
        ]
    )

    investigator = LLMRiskChangeInvestigator(llm_client)

    changes = investigator.investigate(
        project_id="PROJ-001",
        previous_risks=[],
        current_risks=[current_risk],
        evidence=evidence,
    )

    assert len(changes) == 1
    assert changes[0].change_type == RiskChangeType.NEW
    assert changes[0].previous_risk is None
    assert changes[0].current_risk == current_risk


def test_investigate_identifies_resolved_risk(
    llm_client: Mock,
    previous_risk: RiskSignal,
    evidence: list[Evidence],
) -> None:
    llm_client.generate.return_value = json.dumps(
        [
            {
                "change_type": "resolved",
                "previous_risk_signal_id": "RISK-PREV-001",
                "current_risk_signal_id": None,
                "evidence_source_id": "JIRA-002",
                "rationale": (
                    "The latest update confirms that the credential "
                    "blocker has been resolved."
                ),
            }
        ]
    )

    investigator = LLMRiskChangeInvestigator(llm_client)

    changes = investigator.investigate(
        project_id="PROJ-001",
        previous_risks=[previous_risk],
        current_risks=[],
        evidence=evidence,
    )

    assert len(changes) == 1
    assert changes[0].change_type == RiskChangeType.RESOLVED
    assert changes[0].previous_risk == previous_risk
    assert changes[0].current_risk is None


def test_investigate_rejects_invalid_json(
    llm_client: Mock,
    previous_risk: RiskSignal,
    current_risk: RiskSignal,
    evidence: list[Evidence],
) -> None:
    llm_client.generate.return_value = "not valid json"

    investigator = LLMRiskChangeInvestigator(llm_client)

    with pytest.raises(
        ValueError,
        match="LLM risk-change response must contain valid JSON",
    ):
        investigator.investigate(
            project_id="PROJ-001",
            previous_risks=[previous_risk],
            current_risks=[current_risk],
            evidence=evidence,
        )


def test_investigate_rejects_non_array_response(
    llm_client: Mock,
    previous_risk: RiskSignal,
    current_risk: RiskSignal,
    evidence: list[Evidence],
) -> None:
    llm_client.generate.return_value = json.dumps(
        {
            "change_type": "continuing",
        }
    )

    investigator = LLMRiskChangeInvestigator(llm_client)

    with pytest.raises(
        ValueError,
        match="LLM risk-change response must be a JSON array",
    ):
        investigator.investigate(
            project_id="PROJ-001",
            previous_risks=[previous_risk],
            current_risks=[current_risk],
            evidence=evidence,
        )


def test_investigate_rejects_unknown_previous_signal(
    llm_client: Mock,
    current_risk: RiskSignal,
    evidence: list[Evidence],
) -> None:
    llm_client.generate.return_value = json.dumps(
        [
            {
                "change_type": "continuing",
                "previous_risk_signal_id": "UNKNOWN",
                "current_risk_signal_id": "RISK-CURRENT-001",
                "evidence_source_id": "JIRA-002",
                "rationale": "The risk continues.",
            }
        ]
    )

    investigator = LLMRiskChangeInvestigator(llm_client)

    changes = investigator.investigate(
        project_id="PROJ-001",
        previous_risks=[],
        current_risks=[current_risk],
        evidence=evidence,
    )

    assert changes == []


def test_investigate_rejects_unknown_current_signal(
    llm_client: Mock,
    previous_risk: RiskSignal,
    evidence: list[Evidence],
) -> None:
    llm_client.generate.return_value = json.dumps(
        [
            {
                "change_type": "continuing",
                "previous_risk_signal_id": "RISK-PREV-001",
                "current_risk_signal_id": "UNKNOWN",
                "evidence_source_id": "JIRA-002",
                "rationale": "The risk continues.",
            }
        ]
    )

    investigator = LLMRiskChangeInvestigator(llm_client)

    changes = investigator.investigate(
        project_id="PROJ-001",
        previous_risks=[previous_risk],
        current_risks=[],
        evidence=evidence,
    )

    assert changes == []


def test_investigate_rejects_unknown_evidence_source(
    llm_client: Mock,
    previous_risk: RiskSignal,
    current_risk: RiskSignal,
    evidence: list[Evidence],
) -> None:
    llm_client.generate.return_value = json.dumps(
        [
            {
                "change_type": "continuing",
                "previous_risk_signal_id": "RISK-PREV-001",
                "current_risk_signal_id": "RISK-CURRENT-001",
                "evidence_source_id": "UNKNOWN-SOURCE",
                "rationale": "The risk continues.",
            }
        ]
    )

    investigator = LLMRiskChangeInvestigator(llm_client)

    changes = investigator.investigate(
        project_id="PROJ-001",
        previous_risks=[previous_risk],
        current_risks=[current_risk],
        evidence=evidence,
    )

    assert changes == []


def test_investigate_returns_empty_without_evidence(
    llm_client: Mock,
    previous_risk: RiskSignal,
    current_risk: RiskSignal,
) -> None:
    investigator = LLMRiskChangeInvestigator(llm_client)

    changes = investigator.investigate(
        project_id="PROJ-001",
        previous_risks=[previous_risk],
        current_risks=[current_risk],
        evidence=[],
    )

    assert changes == []
    llm_client.generate.assert_not_called()


def test_investigate_rejects_empty_project_id(
    llm_client: Mock,
    evidence: list[Evidence],
) -> None:
    investigator = LLMRiskChangeInvestigator(llm_client)

    with pytest.raises(
        ValueError,
        match="project_id cannot be empty",
    ):
        investigator.investigate(
            project_id="   ",
            previous_risks=[],
            current_risks=[],
            evidence=evidence,
        )


def test_build_prompt_contains_risk_history_and_evidence(
    llm_client: Mock,
    previous_risk: RiskSignal,
    current_risk: RiskSignal,
    evidence: list[Evidence],
) -> None:
    investigator = LLMRiskChangeInvestigator(llm_client)

    prompt = investigator._build_prompt(
        project_id="PROJ-001",
        previous_risks=[previous_risk],
        current_risks=[current_risk],
        evidence=evidence,
    )

    assert "PREVIOUS RISKS" in prompt
    assert "CURRENT RISKS" in prompt
    assert "CURRENT PROJECT EVIDENCE" in prompt
    assert "RISK-PREV-001" in prompt
    assert "RISK-CURRENT-001" in prompt
    assert "JIRA-002" in prompt
    assert "same underlying issue" in prompt
    assert "Do not calculate or provide a health score." in prompt