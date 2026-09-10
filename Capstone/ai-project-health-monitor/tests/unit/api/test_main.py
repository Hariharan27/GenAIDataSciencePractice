from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai_project_health_monitor.main import app, lifespan, settings


def test_health_check_returns_liveness_status() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "AI Project Health Monitor",
        "version": "0.1.0",
    }
    

def test_lifespan_starts_and_shuts_down_health_monitor_scheduler() -> None:
    container = Mock()

    settings.health_monitoring_enabled = True
    settings.health_monitoring_interval_minutes = 60

    with (
        patch(
            "ai_project_health_monitor.main.get_application_container",
            return_value=container,
        ),
        patch("ai_project_health_monitor.main.settings.health_monitoring_enabled", True),
        patch(
            "ai_project_health_monitor.main.settings.health_monitoring_interval_minutes",
            60,
        ),
    ):
        test_app = FastAPI(lifespan=lifespan)

        with TestClient(test_app):
            container.health_monitor_scheduler.start.assert_called_once_with(
                project_ids=["PROJ-001"],
                interval_minutes=60,
            )

        container.health_monitor_scheduler.shutdown.assert_called_once()