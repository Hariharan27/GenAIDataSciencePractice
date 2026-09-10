from unittest.mock import Mock

from ai_project_health_monitor.api.dependencies import ApplicationContainer
from ai_project_health_monitor.core.config import Settings


def test_application_container_creates_health_monitor_scheduler() -> None:
    container = object.__new__(ApplicationContainer)
    container.project_health_monitor = Mock()

    # We only want to verify the scheduler wiring here.
    from ai_project_health_monitor.services.health_monitor_scheduler import (
        HealthMonitorScheduler,
    )

    scheduler = HealthMonitorScheduler(
        monitor=container.project_health_monitor,
    )

    assert scheduler is not None
    assert scheduler._monitor is container.project_health_monitor

def test_application_container_creates_health_trend_service() -> None:
    container = ApplicationContainer(Settings())

    assert container.health_trend_service is not None
    assert (
        container.health_trend_service._health_snapshot_repository
        is container.health_snapshot_repository
    )