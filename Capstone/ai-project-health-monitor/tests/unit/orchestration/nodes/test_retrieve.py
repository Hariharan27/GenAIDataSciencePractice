from unittest.mock import Mock

from ai_project_health_monitor.orchestration.nodes.retrieve import RetrieveNode
from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.rag.models.retrieval import RetrievalResult
from ai_project_health_monitor.rag.project_health_retrieval import (
    ProjectHealthEvidenceRetriever,
)


def test_retrieve_node_returns_retrieval_results() -> None:
    evidence_retriever = Mock(spec=ProjectHealthEvidenceRetriever)
    expected_results = [
        Mock(spec=RetrievalResult),
        Mock(spec=RetrievalResult),
    ]
    evidence_retriever.retrieve.return_value = expected_results

    node = RetrieveNode(
        evidence_retriever=evidence_retriever,
    )

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What risks are affecting the payment API integration?",
    )

    result = node(state)

    assert result["retrieval_results"] == expected_results

    evidence_retriever.retrieve.assert_called_once_with(
        project_id="PROJ-001",
    )