import logging

from ai_project_health_monitor.domain.models.project_health_summary import (
    ProjectHealthSummary,
)
from ai_project_health_monitor.notifications.health_summary_delivery import (
    HealthSummaryDelivery,
)

logger = logging.getLogger(__name__)


class LoggingHealthSummaryDelivery(HealthSummaryDelivery):
    """Delivers project health summaries through application logging."""

    def deliver(self, summary: ProjectHealthSummary) -> None:
        logger.info(
            "PROJECT HEALTH SUMMARY | project_id=%s "
            "| health_score=%.1f | health_status=%s "
            "| executive_summary=%s | top_risks=%s "
            "| recommended_actions=%s",
            summary.project_id,
            summary.health_score,
            summary.health_status.value,
            summary.executive_summary,
            summary.top_risks,
            summary.recommended_actions,
        )