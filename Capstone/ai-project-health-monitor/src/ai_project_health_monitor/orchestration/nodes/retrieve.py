from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.rag.retrieval import RetrievalService


class RetrieveNode:
    """LangGraph node responsible for retrieving relevant project evidence."""

    def __init__(self, retrieval_service: RetrievalService) -> None:
        self._retrieval_service = retrieval_service

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        retrieval_results = self._retrieval_service.retrieve(
            query=state.query,
            project_id=state.project_id,
            limit=5,
        )

        return {
            "retrieval_results": retrieval_results,
        }