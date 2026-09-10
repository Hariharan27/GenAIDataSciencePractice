from pydantic import BaseModel, Field

from ai_project_health_monitor.domain.models.health_score import HealthStatus


class WeeklyHealthAnalysis(BaseModel):
    """Derived health analysis for a project over a weekly period."""

    project_id: str = Field(min_length=1)

    starting_score: float = Field(ge=0.0, le=100.0)
    ending_score: float = Field(ge=0.0, le=100.0)

    score_change: float

    highest_score: float = Field(ge=0.0, le=100.0)
    lowest_score: float = Field(ge=0.0, le=100.0)

    starting_status: HealthStatus
    ending_status: HealthStatus

    observation_count: int = Field(ge=1)

    health_improved: bool
    health_deteriorated: bool