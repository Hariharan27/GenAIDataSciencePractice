from ai_project_health_monitor.rag.models.retrieval import RetrievalResult
from ai_project_health_monitor.rag.retrieval import RetrievalService


class ProjectHealthEvidenceRetriever:
    """Retrieve evidence across the predefined project-health dimensions."""

    HEALTH_ANALYSIS_QUERIES = (
        "What evidence indicates delays, missed milestones, schedule "
        "slippage, or release-date impact?",
        "What blockers, dependencies, or external impediments are "
        "affecting project delivery?",
        "What new or additional requirements have been introduced "
        "beyond the original project scope?",
        "What evidence shows client concern, dissatisfaction, or "
        "negative sentiment about the project?",
        "What testing, quality, defects, or release-readiness issues "
        "could affect project delivery?",
    )

    def __init__(
        self,
        retrieval_service: RetrievalService,
        limit_per_query: int = 5,
    ) -> None:
        if limit_per_query <= 0:
            raise ValueError("limit_per_query must be greater than zero")

        self._retrieval_service = retrieval_service
        self._limit_per_query = limit_per_query

    def retrieve(
        self,
        project_id: str,
    ) -> list[RetrievalResult]:
        """Retrieve and deduplicate evidence relevant to project health."""
        if not project_id.strip():
            raise ValueError("project_id cannot be empty")

        results_by_chunk_id: dict[str, RetrievalResult] = {}

        for query in self.HEALTH_ANALYSIS_QUERIES:
            results = self._retrieval_service.retrieve(
                query=query,
                project_id=project_id,
                limit=self._limit_per_query,
            )

            for result in results:
                chunk_id = result.chunk.chunk_id
                existing = results_by_chunk_id.get(chunk_id)

                if existing is None or result.score > existing.score:
                    results_by_chunk_id[chunk_id] = result

        return list(results_by_chunk_id.values())