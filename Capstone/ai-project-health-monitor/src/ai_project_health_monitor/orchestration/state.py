from pydantic import BaseModel, Field
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.health_score import HealthScore
from ai_project_health_monitor.domain.models.project_health_summary import ProjectHealthSummary
from ai_project_health_monitor.domain.models.risk_group import RiskGroup
from ai_project_health_monitor.domain.models.risk_signal import RiskSignal
from ai_project_health_monitor.rag.models.retrieval import RetrievalResult
from ai_project_health_monitor.domain.models.health_alert import HealthAlert


class ProjectHealthState(BaseModel):
    """State carried through the project health analysis workflow."""

    project_id: str = Field(min_length=1)
    query: str = Field(min_length=1)

    retrieval_results: list[RetrievalResult] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)

    risk_signals: list[RiskSignal] = Field(default_factory=list)
    risk_groups: list[RiskGroup] = Field(default_factory=list)
    primary_risks: list[RiskSignal] = Field(default_factory=list)

    health_score: HealthScore | None = None
    summary: ProjectHealthSummary | None = None
    alert: HealthAlert | None = None
    alert_triggered: bool = False