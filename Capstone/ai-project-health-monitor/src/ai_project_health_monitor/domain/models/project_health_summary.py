from pydantic import BaseModel, Field

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.risk_signal import RiskSeverity, RiskType


class SummaryRisk(BaseModel):
    """A risk highlighted in the project health summary."""
    
    signal_id: str = Field(min_length=1)
    risk_type: RiskType
    severity: RiskSeverity
    rationale: str = Field(min_length=1)


class ProjectHealthSummary(BaseModel):
    """Structured weekly summary of project health."""

    project_id: str = Field(min_length=1)
    health_score: float = Field(ge=0.0, le=100.0)
    health_status: HealthStatus

    executive_summary: str = Field(min_length=1)

    top_risks: list[SummaryRisk] = Field(default_factory=list)

    recommended_actions: list[str] = Field(default_factory=list)