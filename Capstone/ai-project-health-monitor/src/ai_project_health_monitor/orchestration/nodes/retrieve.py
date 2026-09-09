from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.rag.project_health_retrieval import (
    ProjectHealthEvidenceRetriever,
)


class RetrieveNode:
    """LangGraph node responsible for retrieving project health evidence."""

    def __init__(
        self,
        evidence_retriever: ProjectHealthEvidenceRetriever,
    ) -> None:
        self._evidence_retriever = evidence_retriever

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        retrieval_results = self._evidence_retriever.retrieve(
            project_id=state.project_id,
        )
        return {
            "retrieval_results": retrieval_results,
        }