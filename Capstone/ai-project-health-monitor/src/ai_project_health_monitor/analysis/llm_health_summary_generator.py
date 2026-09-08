import json

from pydantic import BaseModel, Field

from ai_project_health_monitor.analysis.health_summary_generator import (
    HealthSummaryGenerator,
)
from ai_project_health_monitor.analysis.llm import LLMClient
from ai_project_health_monitor.domain.models.health_score import HealthScore
from ai_project_health_monitor.domain.models.project_health_summary import (
    ProjectHealthSummary,
    SummaryRisk,
)
from ai_project_health_monitor.domain.models.risk_signal import RiskSignal


class LLMSummaryResponse(BaseModel):
    """Validated narrative content returned by the LLM."""

    executive_summary: str = Field(min_length=1)
    top_risks: list[SummaryRisk] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class LLMHealthSummaryGenerator(HealthSummaryGenerator):
    """Generate project health summaries using an LLM."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    def generate(
        self,
        health_score: HealthScore,
        risk_signals: list[RiskSignal],
    ) -> ProjectHealthSummary:
        prompt = self._build_prompt(
            health_score=health_score,
            risk_signals=risk_signals,
        )

        response = self._llm_client.generate(
            prompt=prompt,
            response_format=self._response_format(),
        )

        parsed = self._parse_response(response)

        self._validate_risk_references(
            parsed.top_risks,
            risk_signals,
        )

        return ProjectHealthSummary(
            project_id=health_score.project_id,
            health_score=health_score.score,
            health_status=health_score.status,
            executive_summary=parsed.executive_summary,
            top_risks=parsed.top_risks,
            recommended_actions=parsed.recommended_actions,
        )

    @staticmethod
    def _response_format() -> dict[str, object]:
        """Return the structured-output schema for supported providers."""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "project_health_summary",
                "schema": {
                    "type": "object",
                    "properties": {
                        "executive_summary": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "top_risks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "signal_id": {
                                        "type": "string",
                                        "minLength": 1,
                                    },
                                    "risk_type": {
                                        "type": "string",
                                    },
                                    "severity": {
                                        "type": "string",
                                    },
                                    "rationale": {
                                        "type": "string",
                                        "minLength": 1,
                                    },
                                },
                                "required": [
                                    "signal_id",
                                    "risk_type",
                                    "severity",
                                    "rationale",
                                ],
                                "additionalProperties": False,
                            },
                        },
                        "recommended_actions": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "minLength": 1,
                            },
                        },
                    },
                    "required": [
                        "executive_summary",
                        "top_risks",
                        "recommended_actions",
                    ],
                    "additionalProperties": False,
                },
            },
        }

    @staticmethod
    def _build_prompt(
        health_score: HealthScore,
        risk_signals: list[RiskSignal],
    ) -> str:
        risks = "\n".join(
            (
                f"- signal_id={signal.signal_id}; "
                f"risk_type={signal.risk_type.value}; "
                f"severity={signal.severity.value}; "
                f"confidence={signal.confidence:.2f}; "
                f"evidence={signal.evidence_quote}"
            )
            for signal in risk_signals
        )

        if not risks:
            risks = "No detected risks."

        return f"""
You are generating a project health summary.

PROJECT HEALTH FACTS
Project ID: {health_score.project_id}
Health Score: {health_score.score:.1f}/100
Health Status: {health_score.status.value}

These values are authoritative. Do not change, recalculate, reinterpret,
or contradict them.

DETECTED RISKS
{risks}

INSTRUCTIONS
1. Write a concise executive summary based only on the supplied facts.
2. Include only risks present in the supplied detected-risk list.
3. For every top risk, preserve the exact signal_id, risk_type, and severity.
4. Do not invent risks, evidence, project facts, dates, metrics, or causes.
5. Recommended actions must be directly relevant to the supplied risks.
6. If there are no risks, return an empty top_risks list.
7. Return only the requested JSON structure.
""".strip()

    @staticmethod
    def _parse_response(response: str) -> LLMSummaryResponse:
        try:
            raw_response = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "LLM summary response must contain valid JSON"
            ) from exc

        return LLMSummaryResponse.model_validate(raw_response)

    @staticmethod
    def _validate_risk_references(
        summary_risks: list[SummaryRisk],
        risk_signals: list[RiskSignal],
    ) -> None:
        available_signal_ids = {
            signal.signal_id
            for signal in risk_signals
        }

        for risk in summary_risks:
            if risk.signal_id not in available_signal_ids:
                raise ValueError(
                    "LLM summary referenced a risk that was not provided: "
                    f"{risk.signal_id}"
                )