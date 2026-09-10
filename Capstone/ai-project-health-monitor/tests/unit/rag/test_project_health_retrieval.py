from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.rag.models.chunk import DocumentChunk
from ai_project_health_monitor.rag.models.retrieval import RetrievalResult
from ai_project_health_monitor.rag.project_health_retrieval import (
    ProjectHealthEvidenceRetriever,
)
from ai_project_health_monitor.rag.retrieval import RetrievalService


def make_result(
    chunk_id: str,
    score: float,
) -> RetrievalResult:
    chunk = DocumentChunk(
        chunk_id=chunk_id,
        project_id="PROJ-001",
        event_id=f"EVT-{chunk_id}",
        source_type=SourceType.JIRA,
        source_id=f"SOURCE-{chunk_id}",
        content=f"Content for {chunk_id}",
        chunk_index=0,
        occurred_at=datetime(2026, 9, 1, tzinfo=UTC),
    )
    return RetrievalResult(
        chunk=chunk,
        score=score,
    )


def test_retrieves_using_all_health_queries() -> None:
    retrieval_service = Mock(spec=RetrievalService)
    retrieval_service.retrieve.side_effect = [
        [make_result("CHUNK-001", 0.90)],
        [make_result("CHUNK-002", 0.85)],
        [make_result("CHUNK-003", 0.88)],
        [make_result("CHUNK-004", 0.91)],
        [make_result("CHUNK-005", 0.87)],
    ]

    retriever = ProjectHealthEvidenceRetriever(
        retrieval_service=retrieval_service,
    )

    results = retriever.retrieve(project_id="PROJ-001")

    assert [result.chunk.chunk_id for result in results] == [
        "CHUNK-001",
        "CHUNK-002",
        "CHUNK-003",
        "CHUNK-004",
        "CHUNK-005",
    ]

    assert retrieval_service.retrieve.call_count == len(
        ProjectHealthEvidenceRetriever.HEALTH_ANALYSIS_QUERIES
    )

    for query in ProjectHealthEvidenceRetriever.HEALTH_ANALYSIS_QUERIES:
        retrieval_service.retrieve.assert_any_call(
            query=query,
            project_id="PROJ-001",
            limit=5,
        )


def test_deduplicates_chunks_and_keeps_highest_score() -> None:
    retrieval_service = Mock(spec=RetrievalService)
    retrieval_service.retrieve.side_effect = [
        [make_result("CHUNK-001", 0.80)],
        [make_result("CHUNK-001", 0.95)],
        [],
        [],
        [],
    ]

    retriever = ProjectHealthEvidenceRetriever(
        retrieval_service=retrieval_service,
    )

    results = retriever.retrieve(project_id="PROJ-001")

    assert len(results) == 1
    assert results[0].chunk.chunk_id == "CHUNK-001"
    assert results[0].score == 0.95


def test_rejects_empty_project_id() -> None:
    retrieval_service = Mock(spec=RetrievalService)

    retriever = ProjectHealthEvidenceRetriever(
        retrieval_service=retrieval_service,
    )

    with pytest.raises(ValueError, match="project_id cannot be empty"):
        retriever.retrieve(project_id="   ")


def test_rejects_invalid_limit() -> None:
    retrieval_service = Mock(spec=RetrievalService)

    with pytest.raises(
        ValueError,
        match="limit_per_query must be greater than zero",
    ):
        ProjectHealthEvidenceRetriever(
            retrieval_service=retrieval_service,
            limit_per_query=0,
        )