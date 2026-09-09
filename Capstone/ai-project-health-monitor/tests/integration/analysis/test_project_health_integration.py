from pathlib import Path

from qdrant_client import QdrantClient

from ai_project_health_monitor.analysis.deterministic_health_scorer import (
    DeterministicHealthScorer,
)
from ai_project_health_monitor.analysis.llm_factory import LLMClientFactory
from ai_project_health_monitor.analysis.llm_risk_analyzer import LLMRiskAnalyzer
from ai_project_health_monitor.analysis.project_health import ProjectHealthService
from ai_project_health_monitor.analysis.risk_consolidator import RiskConsolidator
from ai_project_health_monitor.analysis.risk_grounding_validator import (
    DeterministicRiskGroundingValidator,
)
from ai_project_health_monitor.core.config import get_settings
from ai_project_health_monitor.ingestion.connectors.synthetic_document import (
    SyntheticDocumentConnector,
)
from ai_project_health_monitor.ingestion.connectors.synthetic_email import (
    SyntheticEmailConnector,
)
from ai_project_health_monitor.ingestion.connectors.synthetic_jira import (
    SyntheticJiraConnector,
)
from ai_project_health_monitor.ingestion.service import IngestionService
from ai_project_health_monitor.rag.embeddings.bge import BGEEmbeddingModel
from ai_project_health_monitor.rag.indexing import RAGIndexer
from ai_project_health_monitor.rag.retrieval import RetrievalService
from ai_project_health_monitor.rag.vector_store.qdrant import QdrantVectorStore


def test_project_health_analysis_end_to_end() -> None:
    project_id = "PROJ-001"

    data_dir = Path("data/synthetic")

    ingestion_service = IngestionService(
        connectors=[
            SyntheticJiraConnector(
                data_dir / "jira" / "events.json"
            ),
            SyntheticEmailConnector(
                data_dir / "emails" / "events.json"
            ),
            SyntheticDocumentConnector(
                data_dir / "documents"
            ),
        ]
    )

    embedding_model = BGEEmbeddingModel()

    vector_store = QdrantVectorStore(
        client=QdrantClient(":memory:"),
        vector_size=384,
    )

    indexer = RAGIndexer(
        chunker=__import__(
            "ai_project_health_monitor.rag.chunking",
            fromlist=["FixedSizeChunker"],
        ).FixedSizeChunker(),
        embedding_model=embedding_model,
        vector_store=vector_store,
    )

    retrieval_service = RetrievalService(
        embedding_model=embedding_model,
        vector_store=vector_store,
    )

    events = ingestion_service.ingest_project(project_id)

    assert events

    indexed_count = indexer.index(events)

    assert indexed_count > 0

    query = "What risks are affecting the payment API integration?"

    retrieval_results = retrieval_service.retrieve(
        query=query,
        project_id=project_id,
        limit=5,
    )

    assert retrieval_results

    settings = get_settings()

    llm_client = LLMClientFactory.create(settings)

    risk_analyzer = LLMRiskAnalyzer(
        llm_client=llm_client,
        grounding_validator=DeterministicRiskGroundingValidator(),
    )

    health_scorer = DeterministicHealthScorer()

    health_service = ProjectHealthService(
        risk_analyzer=risk_analyzer,
        health_scorer=health_scorer,
        risk_consolidator=RiskConsolidator(),
    )

    health_score = health_service.analyze(
        project_id=project_id,
        query=query,
        retrieval_results=retrieval_results,
    )

    assert health_score.project_id == project_id
    assert 0.0 <= health_score.score <= 100.0
    assert health_score.status.value in {
        "healthy",
        "at_risk",
        "critical",
    }
    assert health_score.rationale
    assert health_score.contributing_risks