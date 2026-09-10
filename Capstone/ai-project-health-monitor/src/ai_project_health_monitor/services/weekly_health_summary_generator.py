from abc import ABC, abstractmethod

from ai_project_health_monitor.domain.models.risk_signal import RiskSignal
from ai_project_health_monitor.domain.models.weekly_health_analysis import (
    WeeklyHealthAnalysis,
)
from ai_project_health_monitor.domain.models.weekly_health_summary import (
    WeeklyHealthSummary,
)
from ai_project_health_monitor.domain.models.weekly_risk_evolution import (
    WeeklyRiskEvolution,
)


class WeeklyHealthSummaryGenerator(ABC):
    """Generates a human-readable weekly project health summary."""

    @abstractmethod
    def generate(
        self,
        analysis: WeeklyHealthAnalysis,
        key_risks: list[RiskSignal],
        risk_evolution: list[WeeklyRiskEvolution],
    ) -> WeeklyHealthSummary:
        raise NotImplementedError