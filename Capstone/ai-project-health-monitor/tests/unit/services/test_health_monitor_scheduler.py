from unittest.mock import Mock

import pytest

from ai_project_health_monitor.services.health_monitor_scheduler import (
    HealthMonitorScheduler,
)


def test_run_once_analyzes_project() -> None:
    monitor = Mock()
    scheduler = HealthMonitorScheduler(monitor=monitor)

    scheduler.run_once("PROJ-001")

    monitor.analyze.assert_called_once_with("PROJ-001")


def test_run_once_rejects_empty_project_id() -> None:
    monitor = Mock()
    scheduler = HealthMonitorScheduler(monitor=monitor)

    with pytest.raises(ValueError, match="project_id cannot be empty"):
        scheduler.run_once("")

    monitor.analyze.assert_not_called()


def test_run_once_rejects_whitespace_project_id() -> None:
    monitor = Mock()
    scheduler = HealthMonitorScheduler(monitor=monitor)

    with pytest.raises(ValueError, match="project_id cannot be empty"):
        scheduler.run_once("   ")

    monitor.analyze.assert_not_called()


def test_start_schedules_periodic_project_analysis() -> None:
    monitor = Mock()
    scheduler = HealthMonitorScheduler(monitor=monitor)

    scheduler.start(["PROJ-001"], interval_minutes=5)

    job = scheduler._scheduler.get_job("health-monitor-PROJ-001")

    assert job is not None
    assert job.args == ("PROJ-001",)

    scheduler.shutdown()


def test_shutdown_stops_scheduler() -> None:
    monitor = Mock()
    scheduler = HealthMonitorScheduler(monitor=monitor)

    scheduler.start(["PROJ-001"], interval_minutes=5)
    scheduler.shutdown()

    assert not scheduler._scheduler.running


def test_start_rejects_empty_project_id() -> None:
    monitor = Mock()
    scheduler = HealthMonitorScheduler(monitor=monitor)

    with pytest.raises(ValueError, match="project_id cannot be empty"):
        scheduler.start([""], interval_minutes=5)

    assert not scheduler._scheduler.running


def test_start_rejects_non_positive_interval() -> None:
    monitor = Mock()
    scheduler = HealthMonitorScheduler(monitor=monitor)

    with pytest.raises(ValueError, match="interval_minutes must be greater than zero"):
        scheduler.start(["PROJ-001"], interval_minutes=0)

    assert not scheduler._scheduler.running


def test_start_schedules_each_project() -> None:
    monitor = Mock()
    scheduler = HealthMonitorScheduler(monitor=monitor)

    scheduler.start(
        ["PROJ-001", "PROJ-002"],
        interval_minutes=5,
    )

    first_job = scheduler._scheduler.get_job("health-monitor-PROJ-001")
    second_job = scheduler._scheduler.get_job("health-monitor-PROJ-002")

    assert first_job is not None
    assert first_job.args == ("PROJ-001",)

    assert second_job is not None
    assert second_job.args == ("PROJ-002",)

    scheduler.shutdown()