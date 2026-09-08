from ai_project_health_monitor.analysis.health_summary_generator import (
    HealthSummaryGenerator,
)


def test_health_summary_generator_is_abstract() -> None:
    assert HealthSummaryGenerator.__abstractmethods__ == {
        "generate",
    }