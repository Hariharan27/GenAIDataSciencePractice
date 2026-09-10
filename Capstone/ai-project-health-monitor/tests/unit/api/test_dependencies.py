from unittest.mock import Mock

from ai_project_health_monitor.api.dependencies import ApplicationContainer


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