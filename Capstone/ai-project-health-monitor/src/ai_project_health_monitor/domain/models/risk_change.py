from enum import StrEnum

from pydantic import BaseModel, Field

from ai_project_health_monitor.domain.models.risk_signal import RiskSignal


class RiskChangeType(StrEnum):
    """Describes how a project risk changed between health analyses."""

    NEW = "new"
    CONTINUING = "continuing"
    RESOLVED = "resolved"
    SEVERITY_INCREASED = "severity_increased"
    SEVERITY_DECREASED = "severity_decreased"


class RiskChange(BaseModel):
    """Represents a change in a project risk between two analyses."""

    project_id: str = Field(min_length=1)
    change_type: RiskChangeType

    previous_risk: RiskSignal | None = None
    current_risk: RiskSignal | None = None

    rationale: str = Field(min_length=1)