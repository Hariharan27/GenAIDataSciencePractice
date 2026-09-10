from ai_project_health_monitor.domain.models.weekly_health_analysis import (
    WeeklyHealthAnalysis,
)
from ai_project_health_monitor.domain.models.weekly_health_history import (
    WeeklyHealthHistory,
)


class WeeklyHealthAnalysisService:
    """Derives deterministic health metrics from weekly history."""

    def analyze(
        self,
        history: WeeklyHealthHistory,
    ) -> WeeklyHealthAnalysis:
        if not history.snapshots:
            raise ValueError("weekly health history contains no snapshots")

        snapshots = sorted(
            history.snapshots,
            key=lambda snapshot: snapshot.calculated_at,
        )

        starting = snapshots[0]
        ending = snapshots[-1]

        scores = [snapshot.health_score for snapshot in snapshots]

        score_change = ending.health_score - starting.health_score

        return WeeklyHealthAnalysis(
            project_id=history.project_id,
            starting_score=starting.health_score,
            ending_score=ending.health_score,
            score_change=score_change,
            highest_score=max(scores),
            lowest_score=min(scores),
            starting_status=starting.health_status,
            ending_status=ending.health_status,
            observation_count=len(snapshots),
            health_improved=score_change > 0,
            health_deteriorated=score_change < 0,
        )