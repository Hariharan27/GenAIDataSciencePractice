from pydantic import BaseModel, Field

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.risk_signal import RiskSeverity


class HealthEvaluationRisk(BaseModel):
    """Expected risk input for a health-score evaluation case."""

    severity: RiskSeverity
    confidence: float = Field(ge=0.0, le=1.0)


class HealthEvaluationCase(BaseModel):
    """Golden test case for deterministic health-score evaluation."""

    case_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    risks: list[HealthEvaluationRisk]
    expected_score: float = Field(ge=0.0, le=100.0)
    expected_status: HealthStatus


class HealthEvaluationResult(BaseModel):
    """Result of evaluating one health-score case."""

    case_id: str
    expected_score: float
    predicted_score: float
    score_correct: bool
    expected_status: HealthStatus
    predicted_status: HealthStatus
    status_correct: bool


class HealthEvaluationSummary(BaseModel):
    """Aggregate health-score evaluation metrics."""

    total_cases: int = Field(ge=0)
    score_accuracy: float = Field(ge=0.0, le=1.0)
    status_accuracy: float = Field(ge=0.0, le=1.0)


class HealthEvaluationRun(BaseModel):
    """Complete health-score evaluation run."""

    summary: HealthEvaluationSummary
    results: list[HealthEvaluationResult]