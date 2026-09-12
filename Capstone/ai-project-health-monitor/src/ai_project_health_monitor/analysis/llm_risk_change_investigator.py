import json

from pydantic import BaseModel, Field

from ai_project_health_monitor.analysis.llm import LLMClient
from ai_project_health_monitor.analysis.risk_change_investigator import (
    RiskChangeInvestigator,
)
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.risk_change import (
    RiskChange,
    RiskChangeType,
)
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskType,
    RiskSignal,
)


class RiskChangeInvestigationResponse(BaseModel):
    """Validated risk-change decision returned by the LLM."""

    change_type: RiskChangeType
    previous_risk_signal_id: str | None = None
    current_risk_signal_id: str | None = None
    evidence_source_id: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class LLMRiskChangeInvestigator(RiskChangeInvestigator):
    """Investigate project risk evolution using an LLM."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    def investigate(
        self,
        project_id: str,
        previous_risks: list[RiskSignal],
        current_risks: list[RiskSignal],
        evidence: list[Evidence],
    ) -> list[RiskChange]:
        if not project_id.strip():
            raise ValueError("project_id cannot be empty")

        if not evidence:
            return []

        prompt = self._build_prompt(
            project_id=project_id,
            previous_risks=previous_risks,
            current_risks=current_risks,
            evidence=evidence,
        )

        response = self._llm_client.generate(
            prompt=prompt,
            response_format=self._response_format(),
        )

        parsed = self._parse_response(response)

        return self._build_changes(
            project_id=project_id,
            responses=parsed,
            previous_risks=previous_risks,
            current_risks=current_risks,
            evidence=evidence,
        )

    @staticmethod
    def _response_format() -> dict[str, object]:
        """Return the structured-output schema for supported providers."""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "risk_change_investigation",
                "schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "change_type": {
                                "type": "string",
                                "enum": [
                                    change.value
                                    for change in RiskChangeType
                                ],
                            },
                            "previous_risk_signal_id": {
                                "type": ["string", "null"],
                            },
                            "current_risk_signal_id": {
                                "type": ["string", "null"],
                            },
                            "evidence_source_id": {
                                "type": "string",
                                "minLength": 1,
                            },
                            "rationale": {
                                "type": "string",
                                "minLength": 1,
                            },
                        },
                        "required": [
                            "change_type",
                            "previous_risk_signal_id",
                            "current_risk_signal_id",
                            "evidence_source_id",
                            "rationale",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
        }

    @staticmethod
    def _build_prompt(
        project_id: str,
        previous_risks: list[RiskSignal],
        current_risks: list[RiskSignal],
        evidence: list[Evidence],
    ) -> str:
        previous = "\n".join(
            (
                f"- signal_id={risk.signal_id}; "
                f"event_id={risk.event_id}; "
                f"risk_type={risk.risk_type.value}; "
                f"severity={risk.severity.value}; "
                f"evidence={risk.evidence_quote}"
            )
            for risk in previous_risks
        )

        current = "\n".join(
            (
                f"- signal_id={risk.signal_id}; "
                f"event_id={risk.event_id}; "
                f"risk_type={risk.risk_type.value}; "
                f"severity={risk.severity.value}; "
                f"evidence={risk.evidence_quote}"
            )
            for risk in current_risks
        )

        evidence_sections = "\n".join(
            (
                f"Evidence {index}\n"
                f"event_id: {item.event_id}\n"
                f"source_id: {item.source_id}\n"
                f"source_type: {item.source_type.value}\n"
                f"occurred_at: {item.occurred_at.isoformat()}\n"
                f"content: {item.content}"
            )
            for index, item in enumerate(evidence, start=1)
        )

        valid_source_ids = "\n".join(
            f"- {item.source_id}"
            for item in evidence
        )

        return f"""
You are investigating how project risks changed between two health analyses.

PROJECT
-------
{project_id}

PREVIOUS RISKS
--------------
{previous or "No previous risks."}

CURRENT RISKS
-------------
{current or "No current risks."}

CURRENT PROJECT EVIDENCE
------------------------
{evidence_sections}

VALID EVIDENCE SOURCE IDS
-------------------------
{valid_source_ids}

TASK
----
Determine the evolution of the supplied project risks.

Allowed change types:

- new
- continuing
- resolved
- severity_increased
- severity_decreased

IMPORTANT RULES
---------------

1. Use only the supplied risks and evidence.
2. Do not invent a risk.
3. A risk may be considered CONTINUING even when its event_id changes,
   if the evidence clearly indicates that it is the same underlying issue.
4. A risk is NEW only when there is no previous risk representing the same
   underlying issue.
5. A risk is RESOLVED only when the previous issue is no longer supported
   by the current evidence.
6. Severity changes must compare the previous and current severity.
7. Do not infer a severity change without supporting evidence.
8. evidence_source_id MUST exactly match one of the valid evidence source IDs.
9. The rationale must explain the decision using the supplied evidence.
10. Do not calculate or provide a health score.
11. Do not invent project facts, dates, causes, or consequences.
12. Return only the requested JSON array.

SIGNAL REFERENCE RULES
----------------------
- previous_risk_signal_id must refer to a supplied previous risk.
- current_risk_signal_id must refer to a supplied current risk.
- For NEW, previous_risk_signal_id must be null.
- For RESOLVED, current_risk_signal_id must be null.
- For CONTINUING or severity changes, both IDs must be provided.

FINAL GROUNDING RULE
--------------------
Every investigation decision must reference evidence supplied above.
If the evidence does not support the decision, do not return that decision.
""".strip()

    @staticmethod
    def _parse_response(
        response: str,
    ) -> list[RiskChangeInvestigationResponse]:
        try:
            raw_response = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "LLM risk-change response must contain valid JSON"
            ) from exc

        if not isinstance(raw_response, list):
            raise ValueError(
                "LLM risk-change response must be a JSON array"
            )

        return [
            RiskChangeInvestigationResponse.model_validate(item)
            for item in raw_response
        ]

    @staticmethod
    def _build_changes(
        project_id: str,
        responses: list[RiskChangeInvestigationResponse],
        previous_risks: list[RiskSignal],
        current_risks: list[RiskSignal],
        evidence: list[Evidence],
    ) -> list[RiskChange]:
        previous_by_id = {
            risk.signal_id: risk
            for risk in previous_risks
        }
        current_by_id = {
            risk.signal_id: risk
            for risk in current_risks
        }
        evidence_by_source_id = {
            item.source_id: item
            for item in evidence
        }

        changes: list[RiskChange] = []

        for response in responses:
            previous_risk = (
                previous_by_id.get(response.previous_risk_signal_id)
                if response.previous_risk_signal_id
                else None
            )

            current_risk = (
                current_by_id.get(response.current_risk_signal_id)
                if response.current_risk_signal_id
                else None
            )

            if response.evidence_source_id not in evidence_by_source_id:
                continue

            if response.change_type == RiskChangeType.NEW:
                if current_risk is None or previous_risk is not None:
                    continue

            elif response.change_type == RiskChangeType.RESOLVED:
                if previous_risk is None or current_risk is not None:
                    continue

            else:
                if previous_risk is None or current_risk is None:
                    continue

            changes.append(
                RiskChange(
                    project_id=project_id,
                    change_type=response.change_type,
                    previous_risk=previous_risk,
                    current_risk=current_risk,
                    rationale=response.rationale,
                )
            )

        return changes