from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ai_project_health_monitor.api.dependencies import get_application_container
from ai_project_health_monitor.api.routes import router
from ai_project_health_monitor.core.config import get_settings

settings = get_settings()

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    container = get_application_container()
    if settings.health_monitoring_enabled:
        container.health_monitor_scheduler.start(
            project_ids=settings.health_monitoring_project_ids,
            interval_minutes=settings.health_monitoring_interval_minutes,
        )
    try:
        yield
    finally:
        container.health_monitor_scheduler.shutdown()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
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