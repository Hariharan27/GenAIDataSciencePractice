from abc import ABC, abstractmethod

from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.risk_signal import RiskSignal


class RiskAnalyzer(ABC):
    @abstractmethod
    def analyze(
        self,
        project_id: str,
        query: str,
        evidence: list[Evidence],
    ) -> list[RiskSignal]:
        raise NotImplementedError