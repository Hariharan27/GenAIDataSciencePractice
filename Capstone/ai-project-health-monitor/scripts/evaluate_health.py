from datetime import UTC, datetime
from pathlib import Path

from ai_project_health_monitor.analysis.deterministic_health_scorer import (
    DeterministicHealthScorer,
)
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSignal,
    RiskType,
)
from ai_project_health_monitor.evaluation.health import HealthEvaluator
from ai_project_health_monitor.evaluation.loaders import (
    load_health_evaluation_cases,
)
from ai_project_health_monitor.evaluation.models.health import (
    HealthEvaluationRisk,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "data" / "evaluation" / "health_golden.json"


def build_risk_signals(
    case_id: str,
    project_id: str,
    risks: list[HealthEvaluationRisk],
) -> list[RiskSignal]:
    """Convert evaluation risk definitions into domain risk signals."""
    signals: list[RiskSignal] = []

    for index, risk in enumerate(risks, start=1):
        event_id = f"{case_id}-EVENT-{index}"

        evidence = Evidence(
            event_id=event_id,
            source_type=SourceType.JIRA,
            source_id=event_id,
            content="Synthetic evaluation evidence.",
            occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

        signals.append(
            RiskSignal(
                signal_id=f"{case_id}-RISK-{index}",
                project_id=project_id,
                event_id=event_id,
                risk_type=RiskType.BLOCKER,
                severity=risk.severity,
                confidence=risk.confidence,
                evidence=evidence,
                rationale="Synthetic evaluation risk.",
            )
        )

    return signals


def main() -> None:
    cases = load_health_evaluation_cases(DATASET_PATH)

    risk_signals_by_case = {
        case.case_id: build_risk_signals(
            case.case_id,
            case.project_id,
            case.risks,
        )
        for case in cases
    }

    scorer = DeterministicHealthScorer()
    evaluator = HealthEvaluator(scorer.calculate)

    evaluation_run = evaluator.evaluate(
        cases,
        risk_signals_by_case,
    )

    summary = evaluation_run.summary

    print("=" * 72)
    print("HEALTH SCORE EVALUATION")
    print("=" * 72)

    print(f"Total cases     : {summary.total_cases}")
    print(f"Score accuracy  : {summary.score_accuracy:.4f}")
    print(f"Status accuracy : {summary.status_accuracy:.4f}")

    print()
    print("-" * 72)
    print("CASE RESULTS")
    print("-" * 72)

    for result in evaluation_run.results:
        score_status = "PASS" if result.score_correct else "FAIL"
        health_status = "PASS" if result.status_correct else "FAIL"

        print(
            f"{result.case_id} | "
            f"score: expected={result.expected_score:.2f}, "
            f"predicted={result.predicted_score:.2f} [{score_status}] | "
            f"status: expected={result.expected_status}, "
            f"predicted={result.predicted_status} [{health_status}]"
        )

    print()
    print("=" * 72)


if __name__ == "__main__":
    main()