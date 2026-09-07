from unittest.mock import Mock

from ai_project_health_monitor.orchestration.nodes.retrieve import RetrieveNode
from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.rag.models.retrieval import RetrievalResult
from ai_project_health_monitor.rag.retrieval import RetrievalService


def test_retrieve_node_returns_retrieval_results() -> None:
    retrieval_service = Mock(spec=RetrievalService)

    expected_results = [
        Mock(spec=RetrievalResult),
        Mock(spec=RetrievalResult),
    ]

    retrieval_service.retrieve.return_value = expected_results

    node = RetrieveNode(retrieval_service=retrieval_service)

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What risks are affecting the payment API integration?",
    )

    result = node(state)

    assert result["retrieval_results"] == expected_results

    retrieval_service.retrieve.assert_called_once_with(
        query="What risks are affecting the payment API integration?",
        project_id="PROJ-001",
        limit=5,
    )