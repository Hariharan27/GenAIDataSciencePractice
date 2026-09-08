from unittest.mock import Mock

import pytest

from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.notifications.alert_notifier import AlertNotifier
from ai_project_health_monitor.orchestration.nodes.trigger_alert import TriggerAlertNode
from ai_project_health_monitor.orchestration.state import ProjectHealthState


def test_trigger_alert_node_notifies_when_alert_is_triggered() -> None:
    notifier = Mock(spec=AlertNotifier)
    alert = HealthAlert(
        project_id="PROJ-001",
        health_score=30.0,
        health_status=HealthStatus.CRITICAL,
        message="Immediate attention is required.",
        triggered=True,
    )
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What is the current project health?",
        alert=alert,
    )

    node = TriggerAlertNode(notifier=notifier)

    result = node(state)

    assert result == {"alert_triggered": True}
    notifier.notify.assert_called_once_with(alert)


def test_trigger_alert_node_rejects_missing_alert() -> None:
    notifier = Mock(spec=AlertNotifier)
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What is the current project health?",
        alert=None,
    )

    node = TriggerAlertNode(notifier=notifier)

    with pytest.raises(
        ValueError,
        match="alert must be available before triggering alert",
    ):
        node(state)

    notifier.notify.assert_not_called()


def test_trigger_alert_node_rejects_non_triggered_alert() -> None:
    notifier = Mock(spec=AlertNotifier)
    alert = HealthAlert(
        project_id="PROJ-001",
        health_score=75.0,
        health_status=HealthStatus.HEALTHY,
        message="No critical alert required.",
        triggered=False,
    )
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What is the current project health?",
        alert=alert,
    )

    node = TriggerAlertNode(notifier=notifier)

    with pytest.raises(
        ValueError,
        match="cannot trigger an alert when alert.triggered is False",
    ):
        node(state)

    notifier.notify.assert_not_called()