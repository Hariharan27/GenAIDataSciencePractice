from datetime import datetime

from pydantic import BaseModel, Field

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.project_health_summary import ProjectHealthSummary
from ai_project_health_monitor.domain.models.risk_signal import RiskSeverity, RiskType


class ProjectIndexResponse(BaseModel):
    """Response returned after indexing a project."""

    project_id: str = Field(min_length=1)
    events_ingested: int = Field(ge=0)
    chunks_indexed: int = Field(ge=0)


class RiskSignalResponse(BaseModel):
    """Public representation of a detected project risk."""

    signal_id: str
    risk_type: RiskType
    severity: RiskSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_quote: str
    rationale: str


class ProjectHealthResponse(BaseModel):
    """Public response returned by the project health API."""

    project_id: str
    health_score: float = Field(ge=0.0, le=100.0)
    health_status: HealthStatus
    rationale: str
    risks: list[RiskSignalResponse]
    summary: ProjectHealthSummary | None
    alert_triggered: bool


class HealthTrendResponse(BaseModel):
    """API response for project health trend."""

    project_id: str
    current_score: float
    previous_score: float | None
    current_status: HealthStatus
    score_change: float | None

class WeeklyHealthSummaryResponse(BaseModel):
    """API response for a weekly project health summary."""

    project_id: str
    start_date: datetime
    end_date: datetime

    starting_score: float = Field(ge=0.0, le=100.0)
    ending_score: float = Field(ge=0.0, le=100.0)
    score_change: float

    starting_status: HealthStatus
    ending_status: HealthStatus

    health_improved: bool
    health_deteriorated: bool

    key_risks: list[RiskSignalResponse]

    summary: str
    outlook: str
    recommended_actions: list[str]