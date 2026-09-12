from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

from ai_project_health_monitor.domain.models.health_score import (
    HealthScore,
    HealthStatus,
)
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)
from ai_project_health_monitor.evaluation.end_to_end_runner import (
    EndToEndEvaluationRunner,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState


def make_signal(
    project_id: str,
    risk_type: RiskType,
) -> RiskSignal:
    from ai_project_health_monitor.domain.models.evidence import Evidence
    from ai_project_health_monitor.domain.models.project_event import SourceType

    evidence = Evidence(
        event_id="EVT-TEST-001",
        source_type=SourceType.JIRA,
        source_id="TEST-001",
        content="Synthetic evaluation evidence.",
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    return RiskSignal(
        signal_id="RISK-TEST-001",
        project_id=project_id,
        event_id=evidence.event_id,
        risk_type=risk_type,
        severity=RiskSeverity.LOW,
        confidence=1.0,
        evidence=evidence,
        evidence_quote=evidence.content,
        rationale="Synthetic evaluation risk.",
    )


def make_state(
    project_id: str,
    risk_signals: list[RiskSignal],
    score: float,
) -> ProjectHealthState:
    return ProjectHealthState(
        project_id=project_id,
        query="project health assessment",
        risk_signals=risk_signals,
        health_score=HealthScore(
            project_id=project_id,
            score=score,
            status=HealthStatus.HEALTHY,
            contributing_risks=[
                signal.signal_id for signal in risk_signals
            ],
            calculated_at=datetime(2026, 1, 1, tzinfo=UTC),
            rationale="Synthetic evaluation health score.",
        ),
    )


def test_runner_executes_monitor_once_per_case(
    tmp_path: Path,
) -> None:
    dataset = tmp_path / "golden.json"
    dataset.write_text(
        """
        [
            {
                "case_id": "E2E-001",
                "project_id": "PROJ-001",
                "query": "What risks are affecting the project?",
                "expected_risk_types": ["blocker"],
                "expected_status": "healthy",
                "min_expected_score": 90.0,
                "max_expected_score": 100.0
            },
            {
                "case_id": "E2E-002",
                "project_id": "PROJ-002",
                "query": "What risks are affecting the project?",
                "expected_risk_types": [],
                "expected_status": "healthy",
                "min_expected_score": 90.0,
                "max_expected_score": 100.0
            }
        ]
        """,
        encoding="utf-8",
    )

    monitor = Mock()

    monitor.analyze.side_effect = [
        make_state(
            "PROJ-001",
            [make_signal("PROJ-001", RiskType.BLOCKER)],
            95.0,
        ),
        make_state(
            "PROJ-002",
            [],
            100.0,
        ),
    ]

    runner = EndToEndEvaluationRunner(
        monitor=monitor,
    )

    run = runner.run(dataset)

    assert run.summary.total_cases == 2
    assert monitor.analyze.call_count == 2
    assert [call.args for call in monitor.analyze.call_args_list] == [
        ("PROJ-001",),
        ("PROJ-002",),
    ]

    assert run.results[0].predicted_risk_types == [
        RiskType.BLOCKER,
    ]
    assert run.results[1].predicted_risk_types == []