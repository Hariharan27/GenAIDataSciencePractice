from pydantic import BaseModel, Field

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.risk_signal import RiskSignal


class WeeklyHealthSummary(BaseModel):
    """Generated weekly health summary for a project."""

    project_id: str = Field(min_length=1)

    starting_score: float = Field(ge=0.0, le=100.0)
    ending_score: float = Field(ge=0.0, le=100.0)
    score_change: float

    starting_status: HealthStatus
    ending_status: HealthStatus

    health_improved: bool
    health_deteriorated: bool

    key_risks: list[RiskSignal] = Field(default_factory=list)

    summary: str = Field(min_length=1)
    outlook: str = Field(min_length=1)
    recommended_actions: list[str] = Field(default_factory=list)