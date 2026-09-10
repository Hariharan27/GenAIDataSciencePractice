from enum import StrEnum

from pydantic import BaseModel

from ai_project_health_monitor.domain.models.risk_signal import RiskSignal


class RiskEvolutionStatus(StrEnum):
    """Describes how a risk changed during the weekly period."""

    NEW = "new"
    PERSISTING = "persisting"
    RESOLVED = "resolved"


class WeeklyRiskEvolution(BaseModel):
    """Represents the evolution of a risk during a weekly period."""

    risk: RiskSignal
    status: RiskEvolutionStatus

    first_seen: bool = True
    last_seen: bool = True