from ai_project_health_monitor.domain.models.risk_signal import RiskSignal
from ai_project_health_monitor.domain.models.weekly_health_analysis import (
    WeeklyHealthAnalysis,
)
from ai_project_health_monitor.domain.models.weekly_health_summary import (
    WeeklyHealthSummary,
)
from ai_project_health_monitor.services.weekly_health_summary_generator import (
    WeeklyHealthSummaryGenerator,
)
from ai_project_health_monitor.domain.models.weekly_risk_evolution import (
    WeeklyRiskEvolution,
)


class LLMWeeklyHealthSummaryGenerator(WeeklyHealthSummaryGenerator):
    """Generates weekly health narratives using an LLM."""

    def __init__(self, llm_client) -> None:
        self._llm_client = llm_client

    def generate(
        self,
        analysis: WeeklyHealthAnalysis,
        key_risks: list[RiskSignal],
        risk_evolution: list[WeeklyRiskEvolution],
    ) -> WeeklyHealthSummary:
        prompt = self._build_prompt(
            analysis=analysis,
            key_risks=key_risks,
            risk_evolution=risk_evolution,
        )

        response = self._llm_client.generate(prompt)

        return WeeklyHealthSummary.model_validate_json(response)

    def _build_prompt(
        self,
        analysis: WeeklyHealthAnalysis,
        key_risks: list[RiskSignal],
        risk_evolution: list[WeeklyRiskEvolution],
    ) -> str:
        risks = "\n".join(
            (
                f"- Type: {risk.risk_type.value}\n"
                f"  Severity: {risk.severity.value}\n"
                f"  Confidence: {risk.confidence:.2f}\n"
                f"  Evidence: {risk.evidence_quote}\n"
                f"  Rationale: {risk.rationale}"
            )
            for risk in key_risks
        )
        evolution = "\n".join(
            (
                f"- Type: {item.risk.risk_type.value}\n"
                f"  Status: {item.status.value}\n"
                f"  Severity: {item.risk.severity.value}\n"
                f"  Evidence: {item.risk.evidence_quote}\n"
            )
            for item in risk_evolution
        )

        return f"""
You are a project health reporting assistant.

Generate a concise weekly project health summary using ONLY the
structured facts and explicitly provided risk signals below.

PROJECT:
{analysis.project_id}

HEALTH FACTS:
Starting score: {analysis.starting_score:.1f}
Ending score: {analysis.ending_score:.1f}
Score change: {analysis.score_change:+.1f}
Starting status: {analysis.starting_status.value}
Ending status: {analysis.ending_status.value}
Highest score: {analysis.highest_score:.1f}
Lowest score: {analysis.lowest_score:.1f}
Observations: {analysis.observation_count}

HEALTH DIRECTION:
Improved: {analysis.health_improved}
Deteriorated: {analysis.health_deteriorated}

EXPLICITLY IDENTIFIED RISKS:
{risks or "None"}

RULES:
1. Do not change or recalculate any health score.
2. Do not invent risks.
3. Do not invent project events.
4. Do not claim a risk exists unless it appears in the supplied risks.
5. Base the outlook on the supplied health trend and risks.
6. Recommended actions must directly address supplied risks or the observed
   health deterioration.
7. If there are no risks and health is stable, say that the project remains
   stable.
8. Return ONLY valid JSON.

Return exactly this structure:
{{
  "project_id": "{analysis.project_id}",
  "starting_score": {analysis.starting_score},
  "ending_score": {analysis.ending_score},
  "score_change": {analysis.score_change},
  "starting_status": "{analysis.starting_status.value}",
  "ending_status": "{analysis.ending_status.value}",
  "health_improved": {str(analysis.health_improved).lower()},
  "health_deteriorated": {str(analysis.health_deteriorated).lower()},
  "key_risks": [],
  "summary": "...",
  "outlook": "...",
  "recommended_actions": ["..."]
}}
""".strip()