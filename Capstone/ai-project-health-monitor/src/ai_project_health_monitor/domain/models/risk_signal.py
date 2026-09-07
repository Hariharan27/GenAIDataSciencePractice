from enum import StrEnum

from pydantic import BaseModel, Field

from ai_project_health_monitor.domain.models.evidence import Evidence


class RiskType(StrEnum):
    """Types of project risks detected by the system."""

    DELAY = "delay"
    BLOCKER = "blocker"
    SCOPE_CREEP = "scope_creep"
    CLIENT_SENTIMENT = "client_sentiment"
    RESOURCE = "resource"
    DEPENDENCY = "dependency"
    DELIVERY = "delivery"


class RiskSeverity(StrEnum):
    """Severity levels assigned to a detected risk."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskSignal(BaseModel):
    signal_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    risk_type: RiskType
    severity: RiskSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: Evidence
    evidence_quote: str = Field(min_length=1)
    rationale: str = Field(min_length=1)