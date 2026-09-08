import pytest
from pydantic import ValidationError

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.project_health_summary import (
    ProjectHealthSummary,
    SummaryRisk,
)
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskType,
)


def test_project_health_summary_accepts_valid_summary() -> None:
    risk = SummaryRisk(
        signal_id="SIG-001",
        risk_type=RiskType.BLOCKER,
        severity=RiskSeverity.HIGH,
        rationale="Payment API integration is blocked.",
    )

    summary = ProjectHealthSummary(
        project_id="PROJ-001",
        health_score=62.0,
        health_status=HealthStatus.AT_RISK,
        executive_summary="Project is at risk due to a payment API blocker.",
        top_risks=[risk],
        recommended_actions=[
            "Escalate the external API dependency.",
        ],
    )

    assert summary.project_id == "PROJ-001"
    assert summary.health_score == 62.0
    assert summary.health_status == HealthStatus.AT_RISK
    assert summary.top_risks == [risk]
    assert summary.recommended_actions == [
        "Escalate the external API dependency.",
    ]


def test_project_health_summary_defaults_optional_lists() -> None:
    summary = ProjectHealthSummary(
        project_id="PROJ-001",
        health_score=100.0,
        health_status=HealthStatus.HEALTHY,
        executive_summary="Project is healthy.",
    )

    assert summary.top_risks == []
    assert summary.recommended_actions == []


@pytest.mark.parametrize(
    "health_score",
    [-0.1, 100.1],
)
def test_project_health_summary_rejects_invalid_health_score(
    health_score: float,
) -> None:
    with pytest.raises(ValidationError):
        ProjectHealthSummary(
            project_id="PROJ-001",
            health_score=health_score,
            health_status=HealthStatus.HEALTHY,
            executive_summary="Project is healthy.",
        )


def test_project_health_summary_rejects_empty_project_id() -> None:
    with pytest.raises(ValidationError):
        ProjectHealthSummary(
            project_id="",
            health_score=100.0,
            health_status=HealthStatus.HEALTHY,
            executive_summary="Project is healthy.",
        )


def test_summary_risk_requires_rationale() -> None:
    with pytest.raises(ValidationError):
        SummaryRisk(
            signal_id="SIG-001",
            risk_type=RiskType.BLOCKER,
            severity=RiskSeverity.HIGH,
            rationale="",
        )