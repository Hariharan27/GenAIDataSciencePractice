from collections.abc import Callable, Sequence

from ai_project_health_monitor.domain.models.health_score import HealthScore
from ai_project_health_monitor.domain.models.risk_signal import RiskSignal
from ai_project_health_monitor.evaluation.models.end_to_end import (
    EndToEndEvaluationCase,
    EndToEndEvaluationResult,
    EndToEndEvaluationRun,
    EndToEndEvaluationSummary,
)


class EndToEndEvaluator:
    """Evaluate the complete risk-analysis-to-health pipeline."""

    def __init__(
        self,
        analyze: Callable[
            [str, Sequence[RiskSignal]],
            HealthScore,
        ],
    ) -> None:
        self._analyze = analyze

    def evaluate_case(
        self,
        case: EndToEndEvaluationCase,
        risk_signals: Sequence[RiskSignal],
    ) -> EndToEndEvaluationResult:
        health_score = self._analyze(
            case.project_id,
            risk_signals,
        )

        predicted_risk_types = {
            signal.risk_type for signal in risk_signals
        }
        expected_risk_types = set(case.expected_risk_types)

        true_positive_count = len(
            predicted_risk_types & expected_risk_types
        )
        false_positive_count = len(
            predicted_risk_types - expected_risk_types
        )
        false_negative_count = len(
            expected_risk_types - predicted_risk_types
        )

        if predicted_risk_types:
            risk_precision = (
                true_positive_count
                / len(predicted_risk_types)
            )
        else:
            risk_precision = (
                1.0
                if not expected_risk_types
                else 0.0
            )

        if expected_risk_types:
            risk_recall = (
                true_positive_count
                / len(expected_risk_types)
            )
        else:
            risk_recall = (
                1.0
                if not predicted_risk_types
                else 0.0
            )

        if risk_precision + risk_recall > 0:
            risk_f1 = (
                2
                * risk_precision
                * risk_recall
                / (risk_precision + risk_recall)
            )
        else:
            risk_f1 = 0.0

        risk_detection_correct = (
            predicted_risk_types == expected_risk_types
        )

        score_in_range = (
            case.min_expected_score
            <= health_score.score
            <= case.max_expected_score
        )

        return EndToEndEvaluationResult(
            case_id=case.case_id,
            expected_risk_types=sorted(
                expected_risk_types,
                key=str,
            ),
            predicted_risk_types=sorted(
                predicted_risk_types,
                key=str,
            ),
            true_positive_count=true_positive_count,
            false_positive_count=false_positive_count,
            false_negative_count=false_negative_count,
            risk_precision=risk_precision,
            risk_recall=risk_recall,
            risk_f1=risk_f1,
            risk_detection_correct=risk_detection_correct,
            expected_status=case.expected_status,
            predicted_status=health_score.status,
            status_correct=(
                health_score.status == case.expected_status
            ),
            min_expected_score=case.min_expected_score,
            max_expected_score=case.max_expected_score,
            predicted_score=health_score.score,
            score_in_range=score_in_range,
        )

    def evaluate(
        self,
        cases: Sequence[EndToEndEvaluationCase],
        risk_signals_by_case: dict[str, Sequence[RiskSignal]],
    ) -> EndToEndEvaluationRun:
        if not cases:
            return EndToEndEvaluationRun(
                summary=EndToEndEvaluationSummary(
                    total_cases=0,
                    true_positive_count=0,
                    false_positive_count=0,
                    false_negative_count=0,
                    risk_precision=0.0,
                    risk_recall=0.0,
                    risk_f1=0.0,
                    risk_detection_accuracy=0.0,
                    status_accuracy=0.0,
                    score_range_accuracy=0.0,
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

        true_positive_count = sum(
            result.true_positive_count
            for result in results
        )
        false_positive_count = sum(
            result.false_positive_count
            for result in results
        )
        false_negative_count = sum(
            result.false_negative_count
            for result in results
        )

        predicted_positive_count = (
            true_positive_count
            + false_positive_count
        )

        expected_positive_count = (
            true_positive_count
            + false_negative_count
        )

        if predicted_positive_count:
            risk_precision = (
                true_positive_count
                / predicted_positive_count
            )
        else:
            risk_precision = (
                1.0
                if expected_positive_count == 0
                else 0.0
            )

        if expected_positive_count:
            risk_recall = (
                true_positive_count
                / expected_positive_count
            )
        else:
            risk_recall = 1.0

        if risk_precision + risk_recall > 0:
            risk_f1 = (
                2
                * risk_precision
                * risk_recall
                / (risk_precision + risk_recall)
            )
        else:
            risk_f1 = 0.0

        risk_detection_accuracy = sum(
            result.risk_detection_correct
            for result in results
        ) / len(results)

        status_accuracy = sum(
            result.status_correct
            for result in results
        ) / len(results)

        score_range_accuracy = sum(
            result.score_in_range
            for result in results
        ) / len(results)

        return EndToEndEvaluationRun(
            summary=EndToEndEvaluationSummary(
                total_cases=len(results),
                true_positive_count=true_positive_count,
                false_positive_count=false_positive_count,
                false_negative_count=false_negative_count,
                risk_precision=risk_precision,
                risk_recall=risk_recall,
                risk_f1=risk_f1,
                risk_detection_accuracy=risk_detection_accuracy,
                status_accuracy=status_accuracy,
                score_range_accuracy=score_range_accuracy,
            ),
            results=results,
        )