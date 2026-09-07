from collections.abc import Callable, Sequence

from ai_project_health_monitor.domain.models.health_score import HealthScore
from ai_project_health_monitor.domain.models.risk_signal import RiskSignal
from ai_project_health_monitor.evaluation.models.health import (
    HealthEvaluationCase,
    HealthEvaluationResult,
    HealthEvaluationRun,
    HealthEvaluationSummary,
)


class HealthEvaluator:
    """Evaluate deterministic project health scores against golden cases."""

    def __init__(
        self,
        calculate: Callable[[str, list[RiskSignal]], HealthScore],
    ) -> None:
        self._calculate = calculate

    def evaluate_case(
        self,
        case: HealthEvaluationCase,
        risk_signals: Sequence[RiskSignal],
    ) -> HealthEvaluationResult:
        health_score: HealthScore = self._calculate(
            case.project_id,
            list(risk_signals),
        )

        score_correct = health_score.score == case.expected_score
        status_correct = health_score.status == case.expected_status

        return HealthEvaluationResult(
            case_id=case.case_id,
            expected_score=case.expected_score,
            predicted_score=health_score.score,
            score_correct=score_correct,
            expected_status=case.expected_status,
            predicted_status=health_score.status,
            status_correct=status_correct,
        )

    def evaluate(
        self,
        cases: Sequence[HealthEvaluationCase],
        risk_signals_by_case: dict[str, Sequence[RiskSignal]],
    ) -> HealthEvaluationRun:
        if not cases:
            return HealthEvaluationRun(
                summary=HealthEvaluationSummary(
                    total_cases=0,
                    score_accuracy=0.0,
                    status_accuracy=0.0,
                ),
                results=[],
            )

        results = [
            self.evaluate_case(
                case,
                risk_signals_by_case.get(case.case_id, []),
            )
            for case in cases
        ]

        score_accuracy = sum(
            result.score_correct
            for result in results
        ) / len(results)

        status_accuracy = sum(
            result.status_correct
            for result in results
        ) / len(results)

        return HealthEvaluationRun(
            summary=HealthEvaluationSummary(
                total_cases=len(results),
                score_accuracy=score_accuracy,
                status_accuracy=status_accuracy,
            ),
            results=results,
        )