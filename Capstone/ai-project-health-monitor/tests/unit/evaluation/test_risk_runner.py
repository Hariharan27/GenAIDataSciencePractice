from unittest.mock import Mock

from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)
from ai_project_health_monitor.evaluation.risk_runner import (
    RiskEvaluationRunner,
)


def make_signal(
    project_id: str,
    evidence: Evidence,
) -> RiskSignal:
    return RiskSignal(
        signal_id="RISK-TEST-001",
        project_id=project_id,
        event_id=evidence.event_id,
        risk_type=RiskType.BLOCKER,
        severity=RiskSeverity.HIGH,
        confidence=1.0,
        evidence=evidence,
        evidence_quote=evidence.content,
        rationale="The integration is explicitly blocked.",
    )


def test_runner_loads_evidence_and_calls_risk_analyzer(tmp_path) -> None:
    dataset = tmp_path / "risk_golden.json"
    dataset.write_text(
        """
        [
            {
                "case_id": "RISK-001",
                "project_id": "PROJ-001",
                "evidence_event_ids": ["EVT-JIRA-001"],
                "expected_risk_types": ["blocker"],
                "expected_severities": ["high"],
                "expected_evidence_event_ids": ["EVT-JIRA-001"]
            }
        ]
        """,
        encoding="utf-8",
    )

    evidence = Evidence(
        event_id="EVT-JIRA-001",
        source_type=SourceType.JIRA,
        source_id="PROJ-101",
        content="Payment integration is blocked.",
        occurred_at="2026-01-01T00:00:00Z",
    )

    evidence_loader = Mock()
    evidence_loader.load_by_event_id.return_value = [evidence]

    risk_analyzer = Mock()
    risk_analyzer.analyze.return_value = [
        make_signal("PROJ-001", evidence),
    ]

    runner = RiskEvaluationRunner(
        risk_analyzer=risk_analyzer,
        evidence_loader=evidence_loader,
    )

    run = runner.run(dataset)

    assert run.summary.total_cases == 1
    assert run.summary.precision == 1.0
    assert run.summary.recall == 1.0
    assert run.summary.f1 == 1.0
    assert run.summary.severity_accuracy == 1.0
    assert run.summary.evidence_accuracy == 1.0

    evidence_loader.load_by_event_id.assert_called_once_with(
        project_id="PROJ-001",
        event_ids=["EVT-JIRA-001"],
    )
    risk_analyzer.analyze.assert_called_once_with(
        "PROJ-001",
        RiskEvaluationRunner.EVALUATION_QUERY,
        [evidence],
    )