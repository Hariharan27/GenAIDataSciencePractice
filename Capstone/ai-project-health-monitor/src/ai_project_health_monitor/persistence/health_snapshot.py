from datetime import datetime

from pydantic import BaseModel, Field

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.risk_signal import RiskSignal


class ProjectHealthSnapshot(BaseModel):
    """Persisted point-in-time project health assessment."""

    project_id: str = Field(min_length=1)
    health_score: float = Field(ge=0.0, le=100.0)
    health_status: HealthStatus
    risk_signals: list[RiskSignal] = Field(default_factory=list)
    evidence_fingerprint: str = Field(min_length=1)
    calculated_at: datetime
    
