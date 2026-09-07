from __future__ import annotations

from abc import ABC, abstractmethod

from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSignal,
    RiskType,
)


class RiskGroundingValidator(ABC):
    """Contract for validating whether an LLM risk is grounded in evidence."""

    @abstractmethod
    def validate(
        self,
        risk: RiskSignal,
        evidence: Evidence,
    ) -> None:
        """Validate that a risk is supported by its evidence."""
        raise NotImplementedError


class DeterministicRiskGroundingValidator(RiskGroundingValidator):
    """Validate risk signals using deterministic evidence rules."""

    _RISK_TERMS: dict[RiskType, tuple[str, ...]] = {
        RiskType.DELAY: (
            "delayed",
            "delay",
            "behind",
            "late",
            "schedule impact",
            "schedule slip",
            "slippage",
        ),
        RiskType.BLOCKER: (
            "blocked",
            "cannot proceed",
            "unable to proceed",
            "preventing progress",
        ),
        RiskType.SCOPE_CREEP: (
            "additional requirement",
            "additional requirements",
            "not included in the original scope",
            "outside the original scope",
            "out of scope",
            "scope change",
        ),
        RiskType.CLIENT_SENTIMENT: (
            "concern",
            "concerned",
            "dissatisfied",
            "frustrated",
            "unhappy",
            "disappointed",
        ),
        RiskType.RESOURCE: (
            "shortage",
            "unavailable",
            "capacity problem",
            "insufficient capacity",
            "lack of resources",
        ),
        RiskType.DEPENDENCY: (
            "depends on",
            "dependency",
            "waiting for",
            "awaiting",
            "external team",
            "vendor",
        ),
        RiskType.DELIVERY: (
            "delivery is at risk",
            "release is at risk",
            "delivery risk",
            "release risk",
            "committed outcome is at risk",
        ),
    }

    def validate(
        self,
        risk: RiskSignal,
        evidence: Evidence,
    ) -> None:
        if risk.evidence.source_id != evidence.source_id:
            raise ValueError(
                "Risk evidence source does not match provided evidence: "
                f"{risk.evidence.source_id}"
            )

        self._validate_quote(risk, evidence)
        self._validate_risk_support(risk, evidence)

    @staticmethod
    def _validate_quote(
        risk: RiskSignal,
        evidence: Evidence,
    ) -> None:
        quote = " ".join(risk.evidence.content.split())
        content = " ".join(evidence.content.split())

        if not quote:
            raise ValueError(
                "Risk evidence quote cannot be empty: "
                f"{evidence.source_id}"
            )

        if quote not in content:
            raise ValueError(
                "Risk evidence quote is not grounded in provided evidence: "
                f"{evidence.source_id}"
            )

    @classmethod
    def _validate_risk_support(
        cls,
        risk: RiskSignal,
        evidence: Evidence,
    ) -> None:
        normalized_content = " ".join(
            evidence.content.lower().split()
        )

        terms = cls._RISK_TERMS.get(risk.risk_type, ())

        if not any(term in normalized_content for term in terms):
            raise ValueError(
                "Risk type is not supported by the provided evidence: "
                f"{risk.risk_type.value} / {evidence.source_id}"
            )