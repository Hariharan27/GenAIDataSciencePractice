from pydantic import BaseModel, Field

from ai_project_health_monitor.domain.models.health_score import HealthStatus


class HealthTrend(BaseModel):
    """Represents the health trend derived from historical snapshots."""

    project_id: str = Field(min_length=1)
    current_score: float = Field(ge=0.0, le=100.0)
    previous_score: float | None = Field(default=None, ge=0.0, le=100.0)
    current_status: HealthStatus
    score_change: float | None = None