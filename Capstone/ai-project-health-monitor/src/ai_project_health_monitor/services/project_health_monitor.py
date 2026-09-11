from langgraph.graph.state import CompiledStateGraph

from ai_project_health_monitor.domain.models.health_trend import HealthTrend
from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.services.health_trend_service import HealthTrendService


class ProjectHealthMonitor:
    """Application service for running a project health assessment."""

    def __init__(
        self,
        graph: CompiledStateGraph[
            ProjectHealthState,
            None,
            ProjectHealthState,
            ProjectHealthState,
        ],
        health_trend_service: HealthTrendService,
    ) -> None:
        self._graph = graph
        self._health_trend_service = health_trend_service

    def analyze(self, project_id: str) -> ProjectHealthState:
        """Run the project health workflow for a project."""
        if not project_id.strip():
            raise ValueError("project_id cannot be empty")

        state = ProjectHealthState(
            project_id=project_id,
            query="project health assessment",
        )

        result = self._graph.invoke(state)

        return ProjectHealthState.model_validate(result)

    def get_trend(self, project_id: str) -> HealthTrend | None:
        """Return the historical health trend for a project."""
        return self._health_trend_service.get_trend(project_id)