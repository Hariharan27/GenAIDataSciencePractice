from pydantic import BaseModel, Field

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.risk_signal import RiskType


class EndToEndEvaluationCase(BaseModel):
    """Golden case for evaluating the complete project-health pipeline."""

    case_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    expected_risk_types: list[RiskType] = Field(default_factory=list)
    expected_status: HealthStatus
    min_expected_score: float = Field(ge=0.0, le=100.0)
    max_expected_score: float = Field(ge=0.0, le=100.0)


class EndToEndEvaluationResult(BaseModel):
    """Result for one end-to-end evaluation case."""

    case_id: str

    expected_risk_types: list[RiskType]
    predicted_risk_types: list[RiskType]

    true_positive_count: int = Field(ge=0)
    false_positive_count: int = Field(ge=0)
    false_negative_count: int = Field(ge=0)

    risk_precision: float = Field(ge=0.0, le=1.0)
    risk_recall: float = Field(ge=0.0, le=1.0)
    risk_f1: float = Field(ge=0.0, le=1.0)

    risk_detection_correct: bool

    expected_status: HealthStatus
    predicted_status: HealthStatus
    status_correct: bool

    min_expected_score: float
    max_expected_score: float
    predicted_score: float
    score_in_range: bool


class EndToEndEvaluationSummary(BaseModel):
    """Aggregate metrics for an end-to-end evaluation run."""

    total_cases: int = Field(ge=0)

    true_positive_count: int = Field(ge=0)
    false_positive_count: int = Field(ge=0)
    false_negative_count: int = Field(ge=0)

    risk_precision: float = Field(ge=0.0, le=1.0)
    risk_recall: float = Field(ge=0.0, le=1.0)
    risk_f1: float = Field(ge=0.0, le=1.0)

    risk_detection_accuracy: float = Field(ge=0.0, le=1.0)
    status_accuracy: float = Field(ge=0.0, le=1.0)
    score_range_accuracy: float = Field(ge=0.0, le=1.0)


class EndToEndEvaluationRun(BaseModel):
    """Complete end-to-end evaluation run."""

    summary: EndToEndEvaluationSummary
    results: list[EndToEndEvaluationResult]