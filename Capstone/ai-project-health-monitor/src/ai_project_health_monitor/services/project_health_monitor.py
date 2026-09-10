from langgraph.graph.state import CompiledStateGraph

from ai_project_health_monitor.orchestration.state import ProjectHealthState


class ProjectHealthMonitor:
    """Application service for running a project health assessment."""

    def __init__(
        self,
        graph: CompiledStateGraph,
    ) -> None:
        self._graph = graph

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