from datetime import UTC, datetime
from unittest.mock import patch

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.domain.models.project_health_summary import (
    ProjectHealthSummary,
)
from ai_project_health_monitor.notifications.logging_health_summary_delivery import (
    LoggingHealthSummaryDelivery,
)


def test_logging_health_summary_delivery_logs_summary() -> None:
    summary = ProjectHealthSummary(
        project_id="PROJ-001",
        health_score=60.0,
        health_status=HealthStatus.AT_RISK,
        executive_summary="Project has significant delivery risks.",
        top_risks=[],
        recommended_actions=[],
    )

    delivery = LoggingHealthSummaryDelivery()

    with patch(
        "ai_project_health_monitor.notifications.logging_health_summary_delivery.logger"
    ) as logger:
        delivery.deliver(summary)

    logger.info.assert_called_once_with(
        "PROJECT HEALTH SUMMARY | project_id=%s "
        "| health_score=%.1f | health_status=%s "
        "| executive_summary=%s | top_risks=%s "
        "| recommended_actions=%s",
        "PROJ-001",
        60.0,
        "at_risk",
        "Project has significant delivery risks.",
        [],
        [],
    )