from pathlib import Path

from ai_project_health_monitor.api.dependencies import (
    get_application_container,
)
from ai_project_health_monitor.evaluation.evidence_loader import (
    EvaluationEvidenceLoader,
)
from ai_project_health_monitor.evaluation.risk_runner import (
    RiskEvaluationRunner,
)
from ai_project_health_monitor.ingestion.connectors.synthetic_email import (
    SyntheticEmailConnector,
)
from ai_project_health_monitor.ingestion.connectors.synthetic_jira import (
    SyntheticJiraConnector,
)


def main() -> None:
    container = get_application_container()

    jira_connector = SyntheticJiraConnector(
        source_path=Path(container.settings.jira_source_path),
    )
    email_connector = SyntheticEmailConnector(
        source_path=Path(container.settings.email_source_path),
    )

    evidence_loader = EvaluationEvidenceLoader(
        jira_connector=jira_connector,
        email_connector=email_connector,
    )

    runner = RiskEvaluationRunner(
        risk_analyzer=container.risk_analyzer,
        evidence_loader=evidence_loader,
    )

    result = runner.run(
        Path("data/evaluation/risk_golden.json"),
    )

    print("\n" + "=" * 80)
    print("RISK EVALUATION")
    print("=" * 80)

    print(f"Cases             : {result.summary.total_cases}")
    print(f"Precision         : {result.summary.precision:.4f}")
    print(f"Recall            : {result.summary.recall:.4f}")
    print(f"F1                : {result.summary.f1:.4f}")
    print(f"Severity accuracy : {result.summary.severity_accuracy:.4f}")
    print(f"Evidence accuracy : {result.summary.evidence_accuracy:.4f}")

    print("\nCASE RESULTS")
    print("=" * 80)

    for case_result in result.results:
        print(f"\n{case_result.case_id}")
        print(f"  Expected risks  : {case_result.expected_risk_types}")
        print(f"  Predicted risks : {case_result.predicted_risk_types}")
        print(f"  Expected severity  : {case_result.expected_severities}")
        print(f"  Predicted severity : {case_result.predicted_severities}")
        print(f"  Evidence correct   : {case_result.evidence_correct}")


if __name__ == "__main__":
    main()