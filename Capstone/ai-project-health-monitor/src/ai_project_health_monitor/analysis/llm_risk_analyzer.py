import json
from uuid import uuid4

from pydantic import BaseModel, Field

from ai_project_health_monitor.analysis.llm import LLMClient
from ai_project_health_monitor.analysis.risk_analyzer import RiskAnalyzer
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)


class RiskAnalysisResponse(BaseModel):
    """Structured response returned by the risk-analysis model."""

    risk_type: RiskType
    severity: RiskSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_source_id: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class LLMRiskAnalyzer(RiskAnalyzer):
    """Extract evidence-backed, query-relevant risk signals using an LLM."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    def analyze(
        self,
        project_id: str,
        query: str,
        evidence: list[Evidence],
    ) -> list[RiskSignal]:
        """Analyze evidence for risks directly relevant to the query."""
        if not project_id.strip():
            raise ValueError("project_id cannot be empty")

        if not query.strip():
            raise ValueError("query cannot be empty")

        if not evidence:
            return []

        prompt = self._build_prompt(
            project_id=project_id,
            query=query,
            evidence=evidence,
        )

        response = self._llm_client.generate(prompt)

        return self._parse_response(
            project_id=project_id,
            evidence=evidence,
            response=response,
        )

    def _build_prompt(
        self,
        project_id: str,
        query: str,
        evidence: list[Evidence],
    ) -> str:
        evidence_text = "\n\n".join(
            (
                f"Source ID: {item.source_id}\n"
                f"Source Type: {item.source_type.value}\n"
                f"Occurred At: {item.occurred_at.isoformat()}\n"
                f"Content: {item.content}"
            )
            for item in evidence
        )

        return f"""
    Analyze the following project evidence for project {project_id}.

    User query:
    {query}

    Your task is to identify risks that are directly relevant to the
    user query AND directly supported by the provided evidence.

    Important relevance rule:
    - A risk may exist somewhere in the project evidence but must NOT be
    reported unless it directly answers the user query.
    - Do not report unrelated project risks simply because they appear in
    the evidence.
    - Treat the user query as the scope of the analysis.

    Evidence interpretation:
    - Report a risk when the evidence explicitly states or clearly describes
    that risk.
    - A downstream risk is valid when the evidence explicitly states its
    impact or consequence.
    - Do NOT invent a downstream risk solely because it is logically possible.
    - For example, if evidence says an integration is blocked AND explicitly
    says that the blockage is affecting the planned release date, both
    blocker and delay may be reported when relevant to the user query.
    - If the evidence only says an integration is blocked, do NOT assume that
    a delay exists unless the evidence supports it.
    - Distinguish between an explicitly supported consequence and a merely
    possible consequence.

    Query relevance examples:
    - If the user asks about scope changes:
    - Report scope_creep when supported.
    - Do NOT report unrelated blockers, delays, dependencies, delivery risks,
        or client sentiment unless the query specifically asks about them.
    - If the user asks about delivery risks:
    - Report directly supported blocker, delay, delivery, or other relevant
        risks affecting delivery.
    - A scope change should NOT be reported merely because it could potentially
        cause a future delay.
    - Report scope_creep only if the scope change itself is directly relevant
        to the delivery-risk question and the evidence supports it as a current
        delivery risk.

    Allowed risk types:
    - delay
    - blocker
    - scope_creep
    - client_sentiment
    - resource
    - dependency
    - delivery

    Allowed severity values:
    - low
    - medium
    - high
    - critical

    Each object must contain exactly these fields:
    - risk_type: one of "delay", "blocker", "scope_creep",
    "client_sentiment", "resource", "dependency", "delivery"
    - severity: one of "low", "medium", "high", "critical"
    - confidence: a NUMBER between 0.0 and 1.0, NOT a word or label
    - evidence_source_id: must exactly match one of the provided Source IDs
    - rationale: a concise explanation grounded in the evidence

    Example of a valid confidence value:
    0.95

    Invalid confidence values:
    "high"
    "95%"
    "very confident"

    Important:
    - Do not create multiple signals for the same risk type unless the
    evidence clearly represents separate instances of that risk.
    - Prefer one logical risk signal per risk type.
    - Choose the strongest directly relevant evidence for each risk.
    - Do not infer a risk merely because another related risk exists.
    - However, an explicitly stated downstream impact is valid evidence for
    the corresponding risk when it is relevant to the query.
    - Every reported risk must be traceable to the provided evidence.

    If no risk is directly relevant to the user query and supported by the
    evidence, return an empty JSON array.

    Return ONLY a valid JSON array.
    Do not include Markdown code fences.
    Do not include explanations outside the JSON array.

    Evidence:

    {evidence_text}
    """.strip()

    def _parse_response(
        self,
        project_id: str,
        evidence: list[Evidence],
        response: str,
    ) -> list[RiskSignal]:
        try:
            raw_response = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM response must contain valid JSON") from exc

        if not isinstance(raw_response, list):
            raise ValueError("LLM response must be a JSON array")

        evidence_by_source_id = {
            item.source_id: item
            for item in evidence
        }

        signals: list[RiskSignal] = []

        for item in raw_response:
            parsed = RiskAnalysisResponse.model_validate(item)

            source_evidence = evidence_by_source_id.get(
                parsed.evidence_source_id
            )

            if source_evidence is None:
                raise ValueError(
                    "LLM referenced evidence that was not provided"
                )

            signals.append(
                RiskSignal(
                    signal_id=f"RISK-{uuid4()}",
                    project_id=project_id,
                    event_id=source_evidence.event_id,
                    risk_type=parsed.risk_type,
                    severity=parsed.severity,
                    confidence=parsed.confidence,
                    evidence=source_evidence,
                    rationale=parsed.rationale,
                )
            )

        return signals