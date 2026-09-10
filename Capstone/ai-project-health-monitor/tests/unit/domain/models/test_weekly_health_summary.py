from datetime import datetime

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.weekly_health_summary import (
    WeeklyHealthSummary,
)
from ai_project_health_monitor.persistence.health_snapshot import ProjectHealthSnapshot
from ai_project_health_monitor.persistence.repositories.in_memory_health_snapshot import (
    InMemoryHealthSnapshotRepository,
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
from ai_project_health_monitor.services.weekly_health_summary_service import (
    WeeklyHealthSummaryService,
)
from ai_project_health_monitor.services.weekly_risk_evolution_service import (
    WeeklyRiskEvolutionService,
)


class FakeWeeklyHealthSummaryGenerator(WeeklyHealthSummaryGenerator):
    """Deterministic summary generator for integration testing."""

    def generate(
        self,
        analysis,
        key_risks,
        risk_evolution,
    ) -> WeeklyHealthSummary:
        return WeeklyHealthSummary(
            project_id=analysis.project_id,
            starting_score=analysis.starting_score,
            ending_score=analysis.ending_score,
            score_change=analysis.score_change,
            starting_status=analysis.starting_status,
            ending_status=analysis.ending_status,
            health_improved=analysis.health_improved,
            health_deteriorated=analysis.health_deteriorated,
            key_risks=key_risks,
            summary="Project health deteriorated during the week.",
            outlook="Project requires attention.",
            recommended_actions=["Review project risks."],
        )


def test_weekly_health_summary_uses_persisted_health_history() -> None:
    repository = InMemoryHealthSnapshotRepository()

    repository.save(
        ProjectHealthSnapshot(
            project_id="PROJ-001",
            health_score=82.0,
            health_status=HealthStatus.HEALTHY,
            calculated_at=datetime(2026, 9, 1),
        )
    )

    repository.save(
        ProjectHealthSnapshot(
            project_id="PROJ-001",
            health_score=72.0,
            health_status=HealthStatus.HEALTHY,
            calculated_at=datetime(2026, 9, 4),
        )
    )

    repository.save(
        ProjectHealthSnapshot(
            project_id="PROJ-001",
            health_score=61.0,
            health_status=HealthStatus.AT_RISK,
            calculated_at=datetime(2026, 9, 7),
        )
    )

    history_service = WeeklyHealthHistoryService(repository)
    analysis_service = WeeklyHealthAnalysisService()
    summary_generator = FakeWeeklyHealthSummaryGenerator()
    risk_evolution_service = WeeklyRiskEvolutionService()

    summary_service = WeeklyHealthSummaryService(
        weekly_health_history_service=history_service,
        weekly_health_analysis_service=analysis_service,
        weekly_risk_evolution_service=risk_evolution_service,
        weekly_health_summary_generator=summary_generator,
    )

    summary = summary_service.generate(
        project_id="PROJ-001",
        start_date=datetime(2026, 9, 1),
        end_date=datetime(2026, 9, 7),
        key_risks=[],
    )

    assert summary.project_id == "PROJ-001"
    assert summary.starting_score == 82.0
    assert summary.ending_score == 61.0
    assert summary.score_change == -21.0

    assert summary.starting_status == HealthStatus.HEALTHY
    assert summary.ending_status == HealthStatus.AT_RISK

    assert summary.health_improved is False
    assert summary.health_deteriorated is True