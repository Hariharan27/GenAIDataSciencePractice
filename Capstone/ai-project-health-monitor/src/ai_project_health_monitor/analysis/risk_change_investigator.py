from abc import ABC, abstractmethod

from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.risk_change import RiskChange
from ai_project_health_monitor.domain.models.risk_signal import RiskSignal


class RiskChangeInvestigator(ABC):
    """Contract for investigating how project risks evolve over time."""

    @abstractmethod
    def investigate(
        self,
        project_id: str,
        previous_risks: list[RiskSignal],
        current_risks: list[RiskSignal],
        evidence: list[Evidence],
    ) -> list[RiskChange]:
        """Investigate risk changes using previous state and current evidence."""
        raise NotImplementedError