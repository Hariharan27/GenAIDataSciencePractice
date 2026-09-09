import json
from uuid import uuid4

from pydantic import BaseModel, Field

from ai_project_health_monitor.analysis.llm import LLMClient
from ai_project_health_monitor.analysis.risk_analyzer import RiskAnalyzer
from ai_project_health_monitor.analysis.risk_grounding_validator import (
    RiskGroundingValidator,
)
from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.risk_signal import (
    RiskSeverity,
    RiskSignal,
    RiskType,
)


class RiskAnalysisResponse(BaseModel):
    """Validated structure returned by the LLM."""

    risk_type: RiskType
    severity: RiskSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_source_id: str = Field(min_length=1)
    evidence_quote: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class LLMRiskAnalyzer(RiskAnalyzer):
    """Risk analyzer that extracts grounded risk signals using an LLM."""

    def __init__(
        self,
        llm_client: LLMClient,
        grounding_validator: RiskGroundingValidator,
    ) -> None:
        self._llm_client = llm_client
        self._grounding_validator = grounding_validator

    def analyze(
        self,
        project_id: str,
        query: str,
        evidence: list[Evidence],
    ) -> list[RiskSignal]:
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

        response = self._llm_client.generate(
            prompt,
            response_format=self._response_format(),
        )

        return self._parse_response(
            project_id=project_id,
            evidence=evidence,
            response=response,
        )

    @staticmethod
    def _response_format() -> dict[str, object]:
        """Return the structured-output schema shared by supported providers."""

        return {
            "type": "json_schema",
            "json_schema": {
                "name": "risk_analysis",
                "schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "risk_type": {
                                "type": "string",
                                "enum": [risk.value for risk in RiskType],
                            },
                            "severity": {
                                "type": "string",
                                "enum": [
                                    severity.value
                                    for severity in RiskSeverity
                                ],
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0.0,
                                "maximum": 1.0,
                            },
                            "evidence_source_id": {
                                "type": "string",
                                "minLength": 1,
                            },
                            "evidence_quote": {
                                "type": "string",
                                "minLength": 1,
                            },
                            "rationale": {
                                "type": "string",
                                "minLength": 1,
                            },
                        },
                        "required": [
                            "risk_type",
                            "severity",
                            "confidence",
                            "evidence_source_id",
                            "evidence_quote",
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
        query: str,
        evidence: list[Evidence],
    ) -> str:
        evidence_sections: list[str] = []

        for index, item in enumerate(evidence, start=1):
            evidence_sections.append(
                "\n".join(
                    [
                        f"Evidence {index}",
                        f"event_id: {item.event_id}",
                        f"source_type: {item.source_type.value}",
                        f"source_id: {item.source_id}",
                        f"occurred_at: {item.occurred_at.isoformat()}",
                        f"content: {item.content}",
                    ]
                )
            )

        valid_source_ids = "\n".join(
            f"- {item.source_id}" for item in evidence
        )

        return f"""
    You are a project health risk analysis system.

    Project:
    {project_id}

    User query:
    {query}

    Your task is to identify only risks that are directly relevant to the
    user query AND explicitly supported by the provided evidence.

    GROUNDING RULES
    ---------------
    1. Every reported risk MUST be supported by the provided evidence.
    2. The evidence_source_id MUST be copied EXACTLY from the valid evidence
    source IDs listed below.
    3. NEVER invent, modify, abbreviate, or guess an evidence_source_id.
    4. NEVER use an evidence source that was not provided.
    5. If no provided evidence supports a relevant risk, return [].
    6. Do not infer a risk merely because something could potentially cause
    a problem.
    7. Do not use general project knowledge or assumptions.
    8. The rationale must explain why the selected evidence directly supports
    the reported risk.
    9. Do not create a risk from a statement that is merely neutral or
    informational.
    10. Positive project updates must not be converted into risks.

    VALID EVIDENCE SOURCE IDS
    -------------------------
    {valid_source_ids}

    RISK TAXONOMY
    -------------
    DELAY:
    A project task, milestone, or planned activity is explicitly behind
    schedule, late, or delayed.

    BLOCKER:
    Work is explicitly blocked or cannot proceed because of a stated
    blocking condition.

    SCOPE_CREEP:
    A new or additional requirement has been introduced that was not part
    of the original agreed scope.

    CLIENT_SENTIMENT:
    The client explicitly expresses concern, dissatisfaction, frustration,
    or other negative sentiment about the project.

    RESOURCE:
    There is an explicitly stated shortage, unavailability, or capacity
    problem involving people or other project resources.

    DEPENDENCY:
    Progress explicitly depends on another team, system, vendor, approval,
    input, or external condition.

    DELIVERY:
    The project release, delivery, or committed outcome is explicitly
    identified as being at risk.

    IMPORTANT TAXONOMY RULES
    ------------------------
    - Do NOT use DELIVERY as a synonym for DELAY.
    - Do NOT use DELIVERY when the evidence explicitly describes schedule
    slippage or a delay. Use DELAY instead.
    - Do NOT use DELAY merely because a blocker exists.
    - Report DELAY only when the evidence explicitly states that something
    is delayed, behind schedule, late, or has a schedule impact.
    - Report BLOCKER when the evidence explicitly states that work is blocked
    or cannot proceed.
    - Report DELIVERY when the evidence explicitly states that the release,
    delivery, or committed outcome is at risk and the evidence does not
    more precisely describe the situation as a schedule delay.
    - Report SCOPE_CREEP only when an additional or unplanned requirement
    is explicitly stated.
    - Report CLIENT_SENTIMENT only when client concern or negative sentiment
    is explicitly stated.
    - Report RESOURCE only when a resource shortage or capacity problem is
    explicitly stated.
    - Report DEPENDENCY only when progress explicitly depends on another
    entity or condition.
    - Do not infer downstream consequences that are not explicitly stated.

    DOWNSTREAM RISK RULE
    --------------------
    A downstream risk is valid only when the evidence explicitly states
    its impact or consequence.

    For example, if a blocker explicitly states that it is affecting the
    planned release date, the downstream schedule impact is valid and may
    be reported as a DELAY.

    Do not infer downstream consequences that are not explicitly stated.

    EXAMPLE: BLOCKER WITH EXPLICIT RELEASE IMPACT
    ---------------------------------------------
    If evidence says:

    "Payment API integration is blocked because credentials are missing.
    This is affecting the planned release date."

    Then:
    - BLOCKER is supported by the first statement.
    - DELAY is supported by the explicit planned release-date impact.

    The downstream risk is valid because the evidence explicitly states
    its impact or consequence.

    Do not automatically classify this as DELIVERY when the evidence gives
    an explicit schedule impact. DELAY is the more precise taxonomy.

    EXAMPLE: SCOPE CREEP
    --------------------
    If evidence says:

    "The client requested an additional reporting dashboard that was not
    part of the original scope."

    Then:
    - SCOPE_CREEP is supported.

    Do not report DELAY, DELIVERY, or BLOCKER unless the evidence explicitly
    supports those risks as well.

    EXAMPLE: CLIENT SENTIMENT
    -------------------------
    If evidence says:

    "The client is concerned about the repeated delay."

    Then:
    - CLIENT_SENTIMENT is supported.
    - DELAY may also be supported if the evidence explicitly states that
    the project or work is delayed.

    Do not report client sentiment merely because a client is mentioned.

    EXAMPLE: HEALTHY PROJECT
    ------------------------
    If evidence says:

    "Reporting module completed successfully."
    "Release is on track."
    "Performance remains within the planned timeline."

    Return:

    []

    Positive evidence does not constitute a risk.

    QUERY SCOPE RULES
    -----------------
    The query determines the scope of analysis.

    For a specific or narrow query, report only risks directly related to
    the requested topic.

    For a broad project-level query such as:
    - "What are the major delivery risks for this project?"
    - "What are the main risks affecting the project?"
    - "What could impact this project?"

    consider all provided evidence that contains an explicit risk.

    For broad project-level queries:
    - Do not restrict analysis to a single component or activity.
    - Include distinct, materially relevant risk types supported by the
    evidence.
    - Do not omit a risk merely because another risk already exists.
    - Do not create risks that are not explicitly supported.
    - Do not include duplicate representations of the same underlying risk.

    For example, if the evidence explicitly states:
    - a milestone is behind schedule,
    - an integration is blocked,
    - the blocked integration affects the planned release date,

    then a broad delivery-risk query should identify the supported
    BLOCKER and DELAY risks.

    BROAD DELIVERY QUERY RULE
    -------------------------
    When the query asks specifically for "delivery risks", prioritize risks
    that can materially affect schedule, release, or delivery outcome.

    Include:
    - DELAY
    - BLOCKER when the blocked work affects delivery
    - DELIVERY when explicitly supported and no more precise taxonomy applies
    - other risk types only when they are themselves materially relevant to
    delivery and explicitly supported.

    Do not automatically include:
    - CLIENT_SENTIMENT merely because the client is concerned.
    - SCOPE_CREEP merely because a new requirement exists.
    - DEPENDENCY merely because an external dependency exists.

    Those may be contributing factors, but they should not be reported as
    major delivery risks unless the evidence explicitly connects them to
    delivery impact.

    OUTPUT RULES
    ------------
    - Return ONLY a valid JSON array.
    - Do not return markdown.
    - Do not return explanations outside the JSON array.
    - Do not return duplicate risks for the same underlying evidence.
    - Use exactly one of the allowed risk_type values.
    - Use exactly one of the allowed severity values.
    - confidence must be between 0.0 and 1.0.
    - evidence_source_id must exactly match one of the valid source IDs.
    - evidence_quote is REQUIRED for every risk object.
    - evidence_quote MUST be an exact contiguous quote copied from the
    selected evidence content.
    - evidence_quote MUST NOT be paraphrased, summarized, rewritten, or
    generated from reasoning.
    - evidence_quote MUST appear verbatim in the content of the evidence
    identified by evidence_source_id.
    - If you cannot provide an exact quote from the selected evidence,
    DO NOT return that risk.
    - rationale explains why the quoted evidence supports the risk, but
    rationale is NOT a substitute for evidence_quote.
    - Every risk object MUST contain ALL of these fields:
    risk_type
    severity
    confidence
    evidence_source_id
    evidence_quote
    rationale

    EXAMPLE: VALID RISK OBJECT
    --------------------------
    If the provided evidence is:

    source_id: EVT-JIRA-001
    content: Payment API integration is currently blocked because the
    external API team has not provided the required credentials.

    A valid response is:

    [
    {{
        "risk_type": "blocker",
        "severity": "high",
        "confidence": 0.95,
        "evidence_source_id": "EVT-JIRA-001",
        "evidence_quote": (
            "Payment API integration is currently blocked because "
            "the external API team has not provided the required credentials."
        ),
        "rationale": (
            "The payment API integration cannot proceed because "
            "the required external credentials have not been provided."
        ),
    }}
    ]

    IMPORTANT:
    - The example above demonstrates the required output structure.
    - Always copy evidence_quote from the actual provided evidence.
    - Never copy the example quote unless that exact text exists in the
    provided evidence.
    - Before returning each risk object, verify that evidence_quote is
    present in the selected evidence content.

    FINAL EVIDENCE VERIFICATION
    ---------------------------

    Before producing the final JSON response, perform these checks for
    every proposed risk:

    1. The evidence_source_id MUST be one of the VALID EVIDENCE SOURCE IDS
       listed above.
    2. The selected evidence MUST actually support the proposed risk_type.
    3. The evidence_quote MUST be copied exactly from that selected evidence.
    4. If any check fails, remove that risk from the response.
    5. If no risks remain after verification, return [].

    IMPORTANT:
    Do not use information from the example risk object as evidence.
    The example is only a formatting example and is NOT part of the
    provided project evidence.

    EXAMPLE: NO SUPPORTED RISK
    --------------------------

    If no provided evidence supports a relevant risk, return:

    []

    PROVIDED EVIDENCE
    -----------------
    {"\n\n".join(evidence_sections)}
    """.strip()

    @staticmethod
    def _validate_quote(
        evidence_quote: str,
        evidence_content: str,
        evidence_source_id: str,
    ) -> None:
        normalized_quote = " ".join(evidence_quote.split())
        normalized_content = " ".join(evidence_content.split())

        if not normalized_quote:
            raise ValueError(
                "LLM evidence_quote cannot be empty: "
                f"{evidence_source_id}"
            )

        if normalized_quote not in normalized_content:
            raise ValueError(
                "LLM evidence_quote is not grounded in provided evidence: "
                f"{evidence_source_id}"
            )

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
            try:
                parsed = RiskAnalysisResponse.model_validate(item)

                source_evidence = evidence_by_source_id.get(
                    parsed.evidence_source_id
                )

                if source_evidence is None:
                    continue

                self._validate_quote(
                    evidence_quote=parsed.evidence_quote,
                    evidence_content=source_evidence.content,
                    evidence_source_id=parsed.evidence_source_id,
                )

                risk_signal = RiskSignal(
                    signal_id=str(uuid4()),
                    project_id=project_id,
                    event_id=source_evidence.event_id,
                    risk_type=parsed.risk_type,
                    severity=parsed.severity,
                    confidence=parsed.confidence,
                    evidence=source_evidence,
                    evidence_quote=parsed.evidence_quote,
                    rationale=parsed.rationale,
                )

                self._grounding_validator.validate(
                    risk=risk_signal,
                    evidence=source_evidence,
                )

            except (ValueError, TypeError):
                continue

            signals.append(risk_signal)

        return signals