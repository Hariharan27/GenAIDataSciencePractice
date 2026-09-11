from unittest.mock import Mock

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.weekly_health_analysis import (
    WeeklyHealthAnalysis,
)
from ai_project_health_monitor.domain.models.weekly_risk_evolution import (
    WeeklyRiskEvolution,
)
from ai_project_health_monitor.services.llm_weekly_health_summary_generator import (
    LLMWeeklyHealthSummaryGenerator,
)


def test_generate_builds_weekly_summary_from_llm_response() -> None:
    llm_client = Mock()

    llm_client.generate.return_value = """
{
  "project_id": "PROJ-001",
  "starting_score": 82.0,
  "ending_score": 61.0,
  "score_change": -21.0,
  "starting_status": "healthy",
  "ending_status": "at_risk",
  "health_improved": false,
  "health_deteriorated": true,
  "key_risks": [],
  "summary": "Project health deteriorated during the week.",
  "outlook": "Release risk remains elevated.",
  "recommended_actions": [
    "Resolve the payment integration blocker.",
    "Review the release timeline."
  ]
}
"""

    analysis = WeeklyHealthAnalysis(
        project_id="PROJ-001",
        starting_score=82.0,
        ending_score=61.0,
        score_change=-21.0,
        highest_score=82.0,
        lowest_score=61.0,
        starting_status=HealthStatus.HEALTHY,
        ending_status=HealthStatus.AT_RISK,
        observation_count=3,
        health_improved=False,
        health_deteriorated=True,
    )

    generator = LLMWeeklyHealthSummaryGenerator(llm_client)

    risk_evolution: list[WeeklyRiskEvolution] = []

    summary = generator.generate(
        analysis=analysis,
        key_risks=[],
        risk_evolution=risk_evolution,
    )

    assert summary.project_id == "PROJ-001"
    assert summary.starting_score == 82.0
    assert summary.ending_score == 61.0
    assert summary.score_change == -21.0
    assert summary.summary == "Project health deteriorated during the week."
    assert summary.outlook == "Release risk remains elevated."
    assert summary.recommended_actions == [
        "Resolve the payment integration blocker.",
        "Review the release timeline.",
    ]

    llm_client.generate.assert_called_once()

    prompt = llm_client.generate.call_args.args[0]

    assert "Starting score: 82.0" in prompt
    assert "Ending score: 61.0" in prompt
    assert "Score change: -21.0" in prompt
    assert "Do not invent risks." in prompt