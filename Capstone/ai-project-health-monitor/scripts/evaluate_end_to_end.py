from pathlib import Path

from qdrant_client import QdrantClient

from ai_project_health_monitor.analysis.deterministic_health_scorer import (
    DeterministicHealthScorer,
)
from ai_project_health_monitor.analysis.evidence_adapter import EvidenceAdapter
from ai_project_health_monitor.analysis.llm_factory import LLMClientFactory
from ai_project_health_monitor.analysis.llm_risk_analyzer import LLMRiskAnalyzer
from ai_project_health_monitor.analysis.risk_consolidator import RiskConsolidator
from ai_project_health_monitor.core.config import get_settings
from ai_project_health_monitor.evaluation.end_to_end import EndToEndEvaluator
from ai_project_health_monitor.evaluation.loaders import (
    load_end_to_end_evaluation_cases,
)
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
from ai_project_health_monitor.rag.chunking import FixedSizeChunker
from ai_project_health_monitor.rag.embeddings.bge import BGEEmbeddingModel
from ai_project_health_monitor.rag.indexing import RAGIndexer
from ai_project_health_monitor.rag.retrieval import RetrievalService
from ai_project_health_monitor.rag.vector_store.qdrant import QdrantVectorStore

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data" / "synthetic"

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "end_to_end_golden.json"
)


def build_ingestion_service() -> IngestionService:
    return IngestionService(
        connectors=[
            SyntheticJiraConnector(
                DATA_DIR / "jira" / "events.json"
            ),
            SyntheticEmailConnector(
                DATA_DIR / "emails" / "events.json"
            ),
            SyntheticDocumentConnector(
                DATA_DIR / "documents"
            ),
        ]
    )


def main() -> None:
    cases = load_end_to_end_evaluation_cases(DATASET_PATH)

    ingestion_service = build_ingestion_service()

    embedding_model = BGEEmbeddingModel()

    vector_store = QdrantVectorStore(
        client=QdrantClient(":memory:"),
        vector_size=384,
    )

    indexer = RAGIndexer(
        chunker=FixedSizeChunker(),
        embedding_model=embedding_model,
        vector_store=vector_store,
    )

    retrieval_service = RetrievalService(
        embedding_model=embedding_model,
        vector_store=vector_store,
    )

    settings = get_settings()

    llm_client = LLMClientFactory.create(settings)

    risk_analyzer = LLMRiskAnalyzer(
        llm_client=llm_client,
    )

    risk_consolidator = RiskConsolidator()

    health_scorer = DeterministicHealthScorer()

    evaluator = EndToEndEvaluator(
        health_scorer.calculate,
    )

    risk_signals_by_case = {}

    print("=" * 72)
    print("END-TO-END PROJECT HEALTH EVALUATION")
    print("=" * 72)

    print(f"LLM provider : {settings.llm_provider}")
    print(f"LLM model    : {settings.llm_model}")
    print(f"Cases        : {len(cases)}")

    for case in cases:
        print()
        print(f"Running {case.case_id}...")
        print(f"Project : {case.project_id}")
        print(f"Query   : {case.query}")

        events = ingestion_service.ingest_project(
            case.project_id
        )

        indexer.index(events)

        retrieval_results = retrieval_service.retrieve(
            query=case.query,
            project_id=case.project_id,
            limit=5,
        )

        print(
            f"Retrieved chunks : {len(retrieval_results)}"
        )

        print("Retrieved evidence:")

        for index, result in enumerate(
            retrieval_results,
            start=1,
        ):
            chunk = result.chunk

            print(
                f"  {index}. "
                f"score={result.score:.4f} | "
                f"event_id={chunk.event_id} | "
                f"source={chunk.source_type.value} | "
                f"source_id={chunk.source_id}"
            )

            print(
                f"     {chunk.content}"
            )

        evidence = EvidenceAdapter.from_retrieval_results(
            retrieval_results
        )

        risk_signals = risk_analyzer.analyze(
            project_id=case.project_id,
            query=case.query,
            evidence=evidence,
        )

        print("Risk signal details:")

        for signal in risk_signals:
            print(
                f"  - type={signal.risk_type.value} | "
                f"severity={signal.severity.value} | "
                f"confidence={signal.confidence:.2f} | "
                f"event_id={signal.event_id}"
            )

            print(
                f"    evidence={signal.evidence.content}"
            )

            print(
                f"    rationale={signal.rationale}"
            )

        risk_groups = risk_consolidator.consolidate(
            risk_signals
        )

        primary_risks = risk_consolidator.primary_risks(
            risk_groups
        )

        print("Consolidated risk groups:")

        for group in risk_groups:
            print(
                f"  - primary={group.primary_risk.risk_type.value} | "
                f"contributing="
                f"{[signal.risk_type.value for signal in group.contributing_risks]} | "
                f"impact="
                f"{[signal.risk_type.value for signal in group.impact_risks]}"
            )

        risk_signals_by_case[case.case_id] = primary_risks

        print(
            "Detected risks   : "
            f"{[signal.risk_type.value for signal in risk_signals]}"
        )

        print(
            "Scored risks     : "
            f"{[signal.risk_type.value for signal in primary_risks]}"
        )

    evaluation_run = evaluator.evaluate(
        cases,
        risk_signals_by_case,
    )

    summary = evaluation_run.summary

    print()
    print("=" * 72)
    print("EVALUATION RESULTS")
    print("=" * 72)

    print(
        f"Total cases             : "
        f"{summary.total_cases}"
    )

    print(
        "Risk detection accuracy : "
        f"{summary.risk_detection_accuracy:.4f}"
    )

    print(
        "Status accuracy         : "
        f"{summary.status_accuracy:.4f}"
    )

    print(
        "Score range accuracy    : "
        f"{summary.score_range_accuracy:.4f}"
    )

    print()
    print("-" * 72)
    print("CASE RESULTS")
    print("-" * 72)

    for result in evaluation_run.results:
        print(
            f"{result.case_id} | "
            f"risks expected={result.expected_risk_types}, "
            f"predicted={result.predicted_risk_types} | "
            f"status expected={result.expected_status}, "
            f"predicted={result.predicted_status} | "
            f"score={result.predicted_score:.2f}"
        )


if __name__ == "__main__":
    main()