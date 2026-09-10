from apscheduler.schedulers.background import BackgroundScheduler

from ai_project_health_monitor.services.project_health_monitor import (
    ProjectHealthMonitor,
)


class HealthMonitorScheduler:
    """Schedules periodic project health analysis."""

    def __init__(self, monitor: ProjectHealthMonitor) -> None:
        self._monitor = monitor
        self._scheduler = BackgroundScheduler()

    def run_once(self, project_id: str) -> None:
        """Run one health analysis for a project."""
        if not project_id.strip():
            raise ValueError("project_id cannot be empty")

        self._monitor.analyze(project_id)

    def start(
        self,
        project_ids: list[str],
        interval_minutes: int,
    ) -> None:
        """Start periodic health analysis for projects."""
        if interval_minutes <= 0:
            raise ValueError("interval_minutes must be greater than zero")

        for project_id in project_ids:
            if not project_id.strip():
                raise ValueError("project_id cannot be empty")

            self._scheduler.add_job(
                self.run_once,
                "interval",
                minutes=interval_minutes,
                args=[project_id],
                id=f"health-monitor-{project_id}",
                replace_existing=True,
            )

        self._scheduler.start()

    def shutdown(self) -> None:
        """Stop periodic health analysis."""
        if self._scheduler.running:
            self._scheduler.shutdown()