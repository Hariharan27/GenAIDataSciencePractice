from abc import ABC, abstractmethod

from ai_project_health_monitor.domain.models.health_score import HealthScore
from ai_project_health_monitor.domain.models.risk_signal import RiskSignal
from ai_project_health_monitor.domain.models.project_health_summary import (
    ProjectHealthSummary,
)


class HealthSummaryGenerator(ABC):
    """Contract for generating human-readable project health summaries."""

    @abstractmethod
    def generate(
        self,
        health_score: HealthScore,
        risk_signals: list[RiskSignal],
    ) -> ProjectHealthSummary:
        """Generate a structured project health summary."""
        raise NotImplementedError