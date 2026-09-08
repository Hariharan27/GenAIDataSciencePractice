from unittest.mock import Mock

import pytest

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.project_health_summary import (
    ProjectHealthSummary,
)
from ai_project_health_monitor.notifications.health_summary_notifier import (
    HealthSummaryNotifier,
)
from ai_project_health_monitor.orchestration.nodes.deliver_summary import (
    DeliverSummaryNode,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState


def test_deliver_summary_node_notifies_summary() -> None:
    summary_notifier = Mock(spec=HealthSummaryNotifier)

    summary = ProjectHealthSummary(
        project_id="PROJ-001",
        health_score=60.0,
        health_status=HealthStatus.AT_RISK,
        executive_summary="Project has significant delivery risks.",
        top_risks=[],
        recommended_actions=[],
    )

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What is the current project health?",
        summary=summary,
    )

    node = DeliverSummaryNode(summary_notifier=summary_notifier)

    result = node(state)

    assert result == {}
    summary_notifier.notify.assert_called_once_with(summary)


def test_deliver_summary_node_requires_summary() -> None:
    summary_notifier = Mock(spec=HealthSummaryNotifier)

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What is the current project health?",
    )

    node = DeliverSummaryNode(summary_notifier=summary_notifier)

    with pytest.raises(
        ValueError,
        match="summary must be available before delivering summary",
    ):
        node(state)

    summary_notifier.notify.assert_not_called()