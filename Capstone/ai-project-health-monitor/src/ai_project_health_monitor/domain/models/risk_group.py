from pydantic import BaseModel, Field

from ai_project_health_monitor.domain.models.risk_signal import RiskSignal


class RiskGroup(BaseModel):
    """A logically related group of risk signals."""

    primary_risk: RiskSignal
    contributing_risks: list[RiskSignal] = Field(default_factory=list)
    impact_risks: list[RiskSignal] = Field(default_factory=list)