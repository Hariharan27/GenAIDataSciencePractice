from ai_project_health_monitor.domain.models.risk_signal import RiskSignal
from ai_project_health_monitor.domain.models.weekly_health_history import (
    WeeklyHealthHistory,
)
from ai_project_health_monitor.domain.models.weekly_risk_evolution import (
    RiskEvolutionStatus,
    WeeklyRiskEvolution,
)


class WeeklyRiskEvolutionService:
    """Determines how project risks evolved across a weekly health history."""

    def analyze(
        self,
        history: WeeklyHealthHistory,
    ) -> list[WeeklyRiskEvolution]:
        if not history.snapshots:
            return []

        ordered_snapshots = sorted(
            history.snapshots,
            key=lambda snapshot: snapshot.calculated_at,
        )

        first_snapshot = ordered_snapshots[0]
        latest_snapshot = ordered_snapshots[-1]

        first_risks = self._index_risks(first_snapshot.risk_signals)
        latest_risks = self._index_risks(latest_snapshot.risk_signals)

        evolution: list[WeeklyRiskEvolution] = []

        for risk_key, risk in latest_risks.items():
            status = (
                RiskEvolutionStatus.PERSISTING
                if risk_key in first_risks
                else RiskEvolutionStatus.NEW
            )

            evolution.append(
                WeeklyRiskEvolution(
                    risk=risk,
                    status=status,
                    first_seen=risk_key not in first_risks,
                    last_seen=True,
                )
            )

        for risk_key, risk in first_risks.items():
            if risk_key not in latest_risks:
                evolution.append(
                    WeeklyRiskEvolution(
                        risk=risk,
                        status=RiskEvolutionStatus.RESOLVED,
                        first_seen=True,
                        last_seen=False,
                    )
                )

        return evolution

    @staticmethod
    def _index_risks(
        risks: list[RiskSignal],
    ) -> dict[tuple[str, str, str], RiskSignal]:
        return {
            (
                risk.project_id,
                risk.risk_type.value,
                risk.event_id,
            ): risk
            for risk in risks
        }