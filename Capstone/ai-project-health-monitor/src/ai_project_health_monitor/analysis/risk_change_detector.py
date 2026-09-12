from ai_project_health_monitor.domain.models.risk_change import (
    RiskChange,
    RiskChangeType,
)
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
)


class RiskChangeDetector:
    """Detect deterministic changes between previous and current project risks."""

    SEVERITY_RANK: dict[RiskSeverity, int] = {
        RiskSeverity.LOW: 1,
        RiskSeverity.MEDIUM: 2,
        RiskSeverity.HIGH: 3,
        RiskSeverity.CRITICAL: 4,
    }

    def detect(
        self,
        previous_risks: list[RiskSignal],
        current_risks: list[RiskSignal],
    ) -> list[RiskChange]:
        previous_by_key = {
            self._risk_key(risk): risk
            for risk in previous_risks
        }
        current_by_key = {
            self._risk_key(risk): risk
            for risk in current_risks
        }

        changes: list[RiskChange] = []

        for key, current_risk in current_by_key.items():
            previous_risk = previous_by_key.get(key)

            if previous_risk is None:
                changes.append(
                    RiskChange(
                        project_id=current_risk.project_id,
                        change_type=RiskChangeType.NEW,
                        current_risk=current_risk,
                        rationale="The risk was not present in the previous analysis.",
                    )
                )
                continue

            change_type = self._classify_existing_risk(
                previous_risk,
                current_risk,
            )

            changes.append(
                RiskChange(
                    project_id=current_risk.project_id,
                    change_type=change_type,
                    previous_risk=previous_risk,
                    current_risk=current_risk,
                    rationale=self._build_existing_risk_rationale(
                        change_type,
                        previous_risk,
                        current_risk,
                    ),
                )
            )

        for key, previous_risk in previous_by_key.items():
            if key not in current_by_key:
                changes.append(
                    RiskChange(
                        project_id=previous_risk.project_id,
                        change_type=RiskChangeType.RESOLVED,
                        previous_risk=previous_risk,
                        rationale="The risk was present in the previous analysis but is no longer detected.",
                    )
                )

        return changes

    @staticmethod
    def _risk_key(
        risk: RiskSignal,
    ) -> tuple[str, str, str]:
        return (
            risk.project_id,
            risk.event_id,
            risk.risk_type.value,
        )

    def _classify_existing_risk(
        self,
        previous_risk: RiskSignal,
        current_risk: RiskSignal,
    ) -> RiskChangeType:
        previous_rank = self.SEVERITY_RANK[previous_risk.severity]
        current_rank = self.SEVERITY_RANK[current_risk.severity]

        if current_rank > previous_rank:
            return RiskChangeType.SEVERITY_INCREASED

        if current_rank < previous_rank:
            return RiskChangeType.SEVERITY_DECREASED

        return RiskChangeType.CONTINUING

    @staticmethod
    def _build_existing_risk_rationale(
        change_type: RiskChangeType,
        previous_risk: RiskSignal,
        current_risk: RiskSignal,
    ) -> str:
        if change_type == RiskChangeType.SEVERITY_INCREASED:
            return (
                "The risk continues to be present and its severity increased "
                f"from {previous_risk.severity.value} to "
                f"{current_risk.severity.value}."
            )

        if change_type == RiskChangeType.SEVERITY_DECREASED:
            return (
                "The risk continues to be present and its severity decreased "
                f"from {previous_risk.severity.value} to "
                f"{current_risk.severity.value}."
            )

        return "The risk remains present with the same severity."