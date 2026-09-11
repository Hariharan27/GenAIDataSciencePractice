import json
from pathlib import Path

from ai_project_health_monitor.evaluation.models.end_to_end import (
    EndToEndEvaluationCase,
)
from ai_project_health_monitor.evaluation.models.health import (
    HealthEvaluationCase,
)
from ai_project_health_monitor.evaluation.models.ragas import (
    RagasEvaluationCase,
)
from ai_project_health_monitor.evaluation.models.risk import (
    RiskEvaluationCase,
)


def load_ragas_evaluation_cases(
    path: Path,
) -> list[RagasEvaluationCase]:
    """Load RAGAS evaluation cases from a JSON file."""
    raw_data = _load_json_array(path, "RAGAS evaluation")
    return [
        RagasEvaluationCase.model_validate(item)
        for item in raw_data
    ]


def _load_json_array(path: Path, dataset_name: str) -> list[object]:
    """Load and validate that a JSON dataset contains an array."""
    if not path.exists():
        raise FileNotFoundError(
            f"{dataset_name} dataset not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        raw_data = json.load(file)

    if not isinstance(raw_data, list):
        raise ValueError(
            f"{dataset_name} dataset must contain a JSON array"
        )

    return raw_data


def load_risk_evaluation_cases(
    path: Path,
) -> list[RiskEvaluationCase]:
    """Load risk evaluation cases from a JSON file."""
    raw_data = _load_json_array(path, "Risk evaluation")

    return [
        RiskEvaluationCase.model_validate(item)
        for item in raw_data
    ]


def load_health_evaluation_cases(
    path: Path,
) -> list[HealthEvaluationCase]:
    """Load health evaluation cases from a JSON file."""
    raw_data = _load_json_array(path, "Health evaluation")

    return [
        HealthEvaluationCase.model_validate(item)
        for item in raw_data
    ]

def load_end_to_end_evaluation_cases(
    path: Path,
) -> list[EndToEndEvaluationCase]:
    """Load end-to-end evaluation cases from a JSON file."""
    raw_data = _load_json_array(path, "End-to-end evaluation")

    return [
        EndToEndEvaluationCase.model_validate(item)
        for item in raw_data
    ]