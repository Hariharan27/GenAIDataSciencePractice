from pathlib import Path

from ai_project_health_monitor.analysis.deterministic_health_scorer import (
    DeterministicHealthScorer,
)
from ai_project_health_monitor.domain.models.health_score import HealthScore
from ai_project_health_monitor.domain.models.risk_signal import RiskSignal
from ai_project_health_monitor.evaluation.end_to_end import EndToEndEvaluator
from ai_project_health_monitor.evaluation.loaders import (
    load_end_to_end_evaluation_cases,
)
from ai_project_health_monitor.evaluation.models.end_to_end import (
    EndToEndEvaluationRun,
)
from ai_project_health_monitor.services.project_health_monitor import (
    ProjectHealthMonitor,
)


class EndToEndEvaluationRunner:
    """Run golden end-to-end cases against the production health workflow."""

    def __init__(
        self,
        monitor: ProjectHealthMonitor,
    ) -> None:
        self._monitor = monitor
        self._scorer = DeterministicHealthScorer()

    def run(
        self,
        dataset_path: Path,
    ) -> EndToEndEvaluationRun:
        """Execute the golden dataset against the production workflow."""
        cases = load_end_to_end_evaluation_cases(dataset_path)

        risk_signals_by_case: dict[str, list[RiskSignal]] = {}

        for case in cases:
            state = self._monitor.analyze(case.project_id)

            if state.health_score is None:
                raise ValueError(
                    f"Health score was not produced for case {case.case_id}."
                )

            risk_signals_by_case[case.case_id] = state.risk_signals

        evaluator = EndToEndEvaluator(
            self._calculate_health_score,
        )

        return evaluator.evaluate(
            cases=cases,
            risk_signals_by_case=risk_signals_by_case,
        )

    def _calculate_health_score(
        self,
        project_id: str,
        risk_signals: list[RiskSignal],
    ) -> HealthScore:
        """Recalculate the deterministic score from evaluated risk signals."""
        return self._scorer.calculate(
            project_id,
            risk_signals,
        )