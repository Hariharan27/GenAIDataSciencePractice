from ai_project_health_monitor.domain.models.health_score import HealthScore
from ai_project_health_monitor.orchestration.state import ProjectHealthState


class ReturnPreviousHealthNode:
    """Restore the previous health state without running analysis."""

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        if state.previous_health_snapshot is None:
            raise ValueError(
                "previous_health_snapshot must exist when returning previous health"
            )

        snapshot = state.previous_health_snapshot

        health_score = HealthScore(
            project_id=snapshot.project_id,
            score=snapshot.health_score,
            status=snapshot.health_status,
            contributing_risks=[
                risk.signal_id for risk in snapshot.risk_signals
            ],
            calculated_at=snapshot.calculated_at,
            rationale="Returned from the previously persisted health snapshot.",
        )

        return {
            "health_score": health_score,
            "primary_risks": snapshot.risk_signals,
            "risk_signals": snapshot.risk_signals,
        }