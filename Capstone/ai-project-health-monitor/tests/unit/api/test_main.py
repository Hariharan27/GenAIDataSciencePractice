from fastapi.testclient import TestClient

from ai_project_health_monitor.main import app


def test_health_check_returns_liveness_status() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "AI Project Health Monitor",
        "version": "0.1.0",
    }