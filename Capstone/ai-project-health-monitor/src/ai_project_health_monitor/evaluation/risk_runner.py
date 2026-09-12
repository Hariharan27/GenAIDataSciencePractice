from pathlib import Path

from ai_project_health_monitor.analysis.llm_risk_analyzer import LLMRiskAnalyzer
from ai_project_health_monitor.evaluation.evidence_loader import (
    EvaluationEvidenceLoader,
)
from ai_project_health_monitor.evaluation.loaders import (
    load_risk_evaluation_cases,
)
from ai_project_health_monitor.evaluation.models.risk import RiskEvaluationRun
from ai_project_health_monitor.evaluation.risk import RiskEvaluator


class RiskEvaluationRunner:
    """Run golden risk-analysis cases against the production risk analyzer."""

    EVALUATION_QUERY = (
        "Identify all project risks present in the provided evidence."
    )

    def __init__(
        self,
        risk_analyzer: LLMRiskAnalyzer,
        evidence_loader: EvaluationEvidenceLoader,
    ) -> None:
        self._risk_analyzer = risk_analyzer
        self._evidence_loader = evidence_loader

    def run(
        self,
        dataset_path: Path,
    ) -> RiskEvaluationRun:
        """Execute the golden risk dataset."""
        cases = load_risk_evaluation_cases(dataset_path)

        evidence_by_case = {
            case.case_id: self._evidence_loader.load_by_event_id(
                project_id=case.project_id,
                event_ids=case.evidence_event_ids,
            )
            for case in cases
        }

        def analyze(
            project_id: str,
            evidence: list,
        ):
            return self._risk_analyzer.analyze(
                project_id,
                self.EVALUATION_QUERY,
                evidence,
            )

        evaluator = RiskEvaluator(analyze=analyze)

        return evaluator.evaluate(
            cases=cases,
            evidence_by_case=evidence_by_case,
        )