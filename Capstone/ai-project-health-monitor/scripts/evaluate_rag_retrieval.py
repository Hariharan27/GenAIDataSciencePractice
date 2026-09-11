import json
from pathlib import Path

from qdrant_client import QdrantClient

from ai_project_health_monitor.evaluation.models.retrieval import (
    RetrievalEvaluationCase,
    RetrievalEvaluationSummary,
)
from ai_project_health_monitor.evaluation.retrieval import RetrievalEvaluator
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
from ai_project_health_monitor.rag.pipeline import RAGPipeline
from ai_project_health_monitor.rag.reranking.bge import BGEReranker
from ai_project_health_monitor.rag.reranking.service import RerankingService
from ai_project_health_monitor.rag.retrieval import RetrievalService
from ai_project_health_monitor.rag.vector_store.qdrant import QdrantVectorStore

PROJECT_ROOT = Path(__file__).resolve().parents[1]

JIRA_DATA = PROJECT_ROOT / "data/synthetic/jira/events.json"
EMAIL_DATA = PROJECT_ROOT / "data/synthetic/emails/events.json"
DOCUMENT_DATA = PROJECT_ROOT / "data/synthetic/documents"
GOLDEN_DATA = PROJECT_ROOT / "data/evaluation/retrieval_golden.json"

VECTOR_SIZE = 384
TOP_K = 3


def load_evaluation_cases() -> list[RetrievalEvaluationCase]:
    """Load retrieval evaluation cases from the golden dataset."""
    with GOLDEN_DATA.open(encoding="utf-8") as file:
        raw_cases = json.load(file)

    if not isinstance(raw_cases, list):
        raise ValueError("retrieval golden dataset must contain a JSON array")

    return [
        RetrievalEvaluationCase.model_validate(case)
        for case in raw_cases
    ]


def build_pipeline() -> RAGPipeline:
    """Build a RAG pipeline with optional BGE reranking."""
    ingestion_service = IngestionService(
        connectors=[
            SyntheticJiraConnector(JIRA_DATA),
            SyntheticEmailConnector(EMAIL_DATA),
            SyntheticDocumentConnector(DOCUMENT_DATA),
        ]
    )

    embedding_model = BGEEmbeddingModel()

    vector_store = QdrantVectorStore(
        client=QdrantClient(":memory:"),
        vector_size=VECTOR_SIZE,
    )

    indexer = RAGIndexer(
        chunker=FixedSizeChunker(
            chunk_size=500,
            overlap=50,
        ),
        embedding_model=embedding_model,
        vector_store=vector_store,
    )

    retrieval_service = RetrievalService(
        embedding_model=embedding_model,
        vector_store=vector_store,
    )

    return RAGPipeline(
        ingestion_service=ingestion_service,
        indexer=indexer,
        retrieval_service=retrieval_service,
    )


def evaluate_pipeline(
    pipeline: RAGPipeline,
    cases: list[RetrievalEvaluationCase],
) -> RetrievalEvaluationSummary:
    """Index evaluation projects and return retrieval evaluation results."""
    project_ids = sorted(
        {case.project_id for case in cases}
    )

    for project_id in project_ids:
        pipeline.index_project(project_id)

    evaluator = RetrievalEvaluator(
        lambda query, project_id, limit: pipeline.retrieve(
            query=query,
            project_id=project_id,
            limit=limit,
        )
    )

    return evaluator.evaluate(
        cases=cases,
        k=TOP_K,
    )


def compare_rankings(
    baseline_pipeline: RAGPipeline,
    reranked_pipeline: RAGPipeline,
    cases: list[RetrievalEvaluationCase],
) -> None:
    """Print cases where baseline and reranked rankings differ."""
    print()
    print("=" * 60)
    print("RANKING CHANGES")
    print("=" * 60)

    changes_found = False

    for case in cases:
        baseline_results = baseline_pipeline.retrieve(
            query=case.query,
            project_id=case.project_id,
            limit=TOP_K,
        )

        reranked_results = reranked_pipeline.retrieve(
            query=case.query,
            project_id=case.project_id,
            limit=TOP_K,
        )

        baseline_ids = [
            result.chunk.event_id
            for result in baseline_results
        ]
        reranked_ids = [
            result.chunk.event_id
            for result in reranked_results
        ]

        if baseline_ids == reranked_ids:
            continue

        changes_found = True

        print()
        print(f"Query ID : {case.query_id}")
        print(f"Query    : {case.query}")
        print(f"Project  : {case.project_id}")
        print(f"Relevant : {case.relevant_event_ids}")
        print()
        print("BASELINE")
        for rank, result in enumerate(
            baseline_results,
            start=1,
        ):
            print(
                f"  {rank}. "
                f"{result.chunk.event_id} "
                f"(score={result.score:.4f})"
            )

        print()
        print("RERANKED")
        for rank, result in enumerate(
            reranked_results,
            start=1,
        ):
            print(
                f"  {rank}. "
                f"{result.chunk.event_id} "
                f"(score={result.score:.4f})"
            )

    if not changes_found:
        print("No ranking changes detected.")

    print("=" * 60)


def print_summary(
    title: str,
    summary: RetrievalEvaluationSummary,
) -> None:
    """Print retrieval evaluation metrics."""
    print("=" * 60)
    print(title)
    print("=" * 60)
    print(f"Evaluation cases            : {summary.total_cases}")
    print(f"Top K                       : {TOP_K}")
    print()
    print("POSITIVE RETRIEVAL")
    print(f"Hit Rate                    : {summary.hit_rate:.4f}")
    print(f"Mean Precision@{TOP_K}       : {summary.mean_precision_at_k:.4f}")
    print(f"Mean Recall@{TOP_K}          : {summary.mean_recall_at_k:.4f}")
    print()
    print("NEGATIVE RETRIEVAL")
    print(f"Negative cases              : {summary.negative_cases}")
    print(
        f"Negative false-positive cases: "
        f"{summary.negative_false_positive_cases}"
    )
    print()
    print("ISOLATION")
    print(
        f"Cross-project result count  : "
        f"{summary.cross_project_result_count}"
    )
    print("=" * 60)


def main() -> None:
    """Compare baseline retrieval against BGE reranked retrieval."""
    cases = load_evaluation_cases()

    print("Building baseline retrieval pipeline...")
    baseline_pipeline = build_pipeline()
    baseline_summary = evaluate_pipeline(
        pipeline=baseline_pipeline,
        cases=cases,
    )

    print("Building reranked retrieval pipeline...")
    reranked_pipeline = build_pipeline()
    reranked_summary = evaluate_pipeline(
        pipeline=reranked_pipeline,
        cases=cases,
    )

    compare_rankings(
    baseline_pipeline=baseline_pipeline,
    reranked_pipeline=reranked_pipeline,
    cases=cases,
    )

    print()
    print_summary(
        title="RAG RETRIEVAL BASELINE",
        summary=baseline_summary,
    )

    print()
    print_summary(
        title="RAG RETRIEVAL WITH BGE RERANKING",
        summary=reranked_summary,
    )

    print()
    print("=" * 60)
    print("RERANKING IMPACT")
    print("=" * 60)
    print(
        f"Hit Rate delta              : "
        f"{reranked_summary.hit_rate - baseline_summary.hit_rate:+.4f}"
    )
    print(
        f"Precision@{TOP_K} delta       : "
        f"{reranked_summary.mean_precision_at_k - baseline_summary.mean_precision_at_k:+.4f}"
    )

    baseline_recall = baseline_summary.mean_recall_at_k
    reranked_recall = reranked_summary.mean_recall_at_k

    if baseline_recall is None or reranked_recall is None:
        recall_delta = None
    else:
        recall_delta = reranked_recall - baseline_recall

    print(
        f"Recall@{TOP_K} delta          : "
        f"{recall_delta:+.4f}"
        if recall_delta is not None
        else f"Recall@{TOP_K} delta          : N/A"
    )
    
    negative_fp_delta = (
    reranked_summary.negative_false_positive_cases
    - baseline_summary.negative_false_positive_cases
    )

    print(
        f"Negative FP delta            : "
        f"{negative_fp_delta:+d}"
    )
    cross_project_delta = (
    reranked_summary.cross_project_result_count
    - baseline_summary.cross_project_result_count
    )
    print(
        f"Cross-project leakage delta  : "
        f"{cross_project_delta:+d}"
    )
    print("=" * 60)

    if baseline_summary.cross_project_result_count > 0:
        raise RuntimeError(
            "baseline retrieval evaluation detected cross-project leakage"
        )

    if reranked_summary.cross_project_result_count > 0:
        raise RuntimeError(
            "reranked retrieval evaluation detected cross-project leakage"
        )


if __name__ == "__main__":
    main()