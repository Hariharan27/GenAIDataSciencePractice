from datetime import datetime

from pydantic import BaseModel, Field

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.risk_signal import RiskSignal


class HealthHistoryPoint(BaseModel):
    """A project health observation within a historical period."""

    calculated_at: datetime
    health_score: float = Field(ge=0.0, le=100.0)
    health_status: HealthStatus
    risk_signals: list[RiskSignal] = Field(default_factory=list)


class WeeklyHealthHistory(BaseModel):
    """Historical health data used to generate a weekly project summary."""

    project_id: str = Field(min_length=1)
    start_date: datetime
    end_date: datetime
    snapshots: list[HealthHistoryPoint] = Field(default_factory=list)