from datetime import datetime

from ai_project_health_monitor.domain.models.risk_signal import RiskSignal
from ai_project_health_monitor.domain.models.weekly_health_summary import (
    WeeklyHealthSummary,
)
from ai_project_health_monitor.services.weekly_health_analysis_service import (
    WeeklyHealthAnalysisService,
)
from ai_project_health_monitor.services.weekly_health_history_service import (
    WeeklyHealthHistoryService,
)
from ai_project_health_monitor.services.weekly_health_summary_generator import (
    WeeklyHealthSummaryGenerator,
)
from ai_project_health_monitor.services.weekly_risk_evolution_service import (
    WeeklyRiskEvolutionService,
)


class WeeklyHealthSummaryService:
    """Coordinates historical analysis and weekly summary generation."""

    def __init__(
        self,
        weekly_health_history_service: WeeklyHealthHistoryService,
        weekly_health_analysis_service: WeeklyHealthAnalysisService,
        weekly_health_summary_generator: WeeklyHealthSummaryGenerator,
        weekly_risk_evolution_service: WeeklyRiskEvolutionService,
    ) -> None:
        self._history_service = weekly_health_history_service
        self._analysis_service = weekly_health_analysis_service
        self._summary_generator = weekly_health_summary_generator
        self._risk_evolution_service = weekly_risk_evolution_service

    def generate(
        self,
        project_id: str,
        start_date: datetime,
        end_date: datetime,
        key_risks: list[RiskSignal],
    ) -> WeeklyHealthSummary:
        history = self._history_service.get_history(
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
        )

        analysis = self._analysis_service.analyze(history)

        risk_evolution = self._risk_evolution_service.analyze(history)

        return self._summary_generator.generate(
            analysis=analysis,
            key_risks=key_risks,
            risk_evolution=risk_evolution,
        )