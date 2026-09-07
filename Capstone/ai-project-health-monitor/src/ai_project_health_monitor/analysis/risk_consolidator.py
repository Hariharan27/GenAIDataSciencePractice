from ai_project_health_monitor.domain.models.risk_group import RiskGroup
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSignal,
    RiskType,
)


class RiskConsolidator:
    """Consolidate directly related risk signals into logical risk groups."""

    def consolidate(
        self,
        risk_signals: list[RiskSignal],
    ) -> list[RiskGroup]:
        if not risk_signals:
            return []

        primary_signals = [
            signal
            for signal in risk_signals
            if signal.risk_type != RiskType.DEPENDENCY
        ]

        dependency_signals = [
            signal
            for signal in risk_signals
            if signal.risk_type == RiskType.DEPENDENCY
        ]

        groups: list[RiskGroup] = []

        for primary in primary_signals:
            related_dependencies = [
                signal
                for signal in dependency_signals
                if self._is_related_dependency(
                    primary,
                    signal,
                )
            ]

            groups.append(
                RiskGroup(
                    primary_risk=primary,
                    contributing_risks=related_dependencies,
                    impact_risks=[],
                )
            )

        return groups

    def primary_risks(
        self,
        risk_groups: list[RiskGroup],
    ) -> list[RiskSignal]:
        """Return risks that should be independently scored."""
        return [
            group.primary_risk
            for group in risk_groups
        ]

    @staticmethod
    def _is_related_dependency(
        primary: RiskSignal,
        dependency: RiskSignal,
    ) -> bool:
        """Determine whether a dependency directly supports a primary risk."""
        return (
            primary.project_id == dependency.project_id
            and primary.event_id == dependency.event_id
        )