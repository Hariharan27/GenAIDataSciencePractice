from fastapi import FastAPI

from ai_project_health_monitor.api.routes import router
from ai_project_health_monitor.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

app.include_router(router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return application liveness status."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }