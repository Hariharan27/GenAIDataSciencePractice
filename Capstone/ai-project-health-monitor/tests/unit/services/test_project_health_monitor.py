from contextlib import suppress
from unittest.mock import Mock

from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.services.project_health_monitor import (
    ProjectHealthMonitor,
)


def test_analyze_invokes_graph_and_returns_project_health_state() -> None:
    graph = Mock()
    graph.invoke.return_value = {
        "project_id": "PROJ-001",
        "query": "project health assessment",
    }

    health_trend_service = Mock()
    monitor = ProjectHealthMonitor(
        graph=graph,
        health_trend_service=health_trend_service,
    )

    result = monitor.analyze("PROJ-001")

    assert isinstance(result, ProjectHealthState)
    assert result.project_id == "PROJ-001"
    assert result.query == "project health assessment"

    graph.invoke.assert_called_once()
    invoked_state = graph.invoke.call_args.args[0]

    assert isinstance(invoked_state, ProjectHealthState)
    assert invoked_state.project_id == "PROJ-001"
    assert invoked_state.query == "project health assessment"


def test_analyze_rejects_empty_project_id() -> None:
    graph = Mock()

    health_trend_service = Mock()
    monitor = ProjectHealthMonitor(
        graph=graph,
        health_trend_service=health_trend_service,
    )

    try:
        monitor.analyze("   ")
    except ValueError as exc:
        assert str(exc) == "project_id cannot be empty"
    else:
        raise AssertionError("Expected ValueError")


def test_analyze_does_not_invoke_graph_for_empty_project_id() -> None:
    graph = Mock()

    health_trend_service = Mock()
    monitor = ProjectHealthMonitor(
        graph=graph,
        health_trend_service=health_trend_service,
    )

    with suppress(ValueError):
        monitor.analyze("")

    graph.invoke.assert_not_called()

def test_get_trend_delegates_to_health_trend_service() -> None:
    graph = Mock()
    health_trend_service = Mock()

    expected_trend = Mock()
    health_trend_service.get_trend.return_value = expected_trend

    monitor = ProjectHealthMonitor(
        graph=graph,
        health_trend_service=health_trend_service,
    )

    result = monitor.get_trend("PROJ-001")

    assert result is expected_trend
    health_trend_service.get_trend.assert_called_once_with("PROJ-001")

