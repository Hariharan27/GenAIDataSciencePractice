from pydantic import BaseModel, Field

from ai_project_health_monitor.domain.models.health_score import HealthStatus


class HealthAlert(BaseModel):
    """Alert generated when project health crosses a critical threshold."""

    project_id: str = Field(min_length=1)
    health_score: float = Field(ge=0.0, le=100.0)
    health_status: HealthStatus
    message: str = Field(min_length=1)
    triggered: bool