import asyncio

from pathlib import Path

from qdrant_client import QdrantClient

from ai_project_health_monitor.analysis.llm_factory import LLMClientFactory
from ai_project_health_monitor.core.config import get_settings
from ai_project_health_monitor.evaluation.loaders import load_ragas_evaluation_cases
from ai_project_health_monitor.evaluation.ragas_evaluator import RagasEvaluator
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
from ai_project_health_monitor.rag.retrieval import RetrievalService
from ai_project_health_monitor.rag.vector_store.qdrant import QdrantVectorStore
from ai_project_health_monitor.evaluation.ragas_llm import RagasLLMAdapter


PROJECT_ROOT = Path(__file__).resolve().parents[1]

JIRA_DATA = PROJECT_ROOT / "data/synthetic/jira/events.json"
EMAIL_DATA = PROJECT_ROOT / "data/synthetic/emails/events.json"
DOCUMENT_DATA = PROJECT_ROOT / "data/synthetic/documents"
GOLDEN_DATA = PROJECT_ROOT / "data/evaluation/ragas_golden.json"

VECTOR_SIZE = 384
TOP_K = 3


def build_rag_pipeline() -> tuple[RAGPipeline, BGEEmbeddingModel]:
    """Build the real synthetic-data RAG pipeline for evaluation."""
    ingestion_service = IngestionService(
        connectors=[
            SyntheticJiraConnector(JIRA_DATA),
            SyntheticEmailConnector(EMAIL_DATA),
            SyntheticDocumentConnector(DOCUMENT_DATA),
        ],
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

    pipeline = RAGPipeline(
        ingestion_service=ingestion_service,
        indexer=indexer,
        retrieval_service=retrieval_service,
    )

    return pipeline, embedding_model


def generate_answer(
    *,
    question: str,
    contexts: list[str],
    llm_client,
) -> str:
    """Generate a grounded answer from the retrieved contexts."""
    context_text = "\n\n".join(
        f"[Context {index}]\n{context}"
        for index, context in enumerate(contexts, start=1)
    )

    prompt = f"""
You are answering a project-health question using only the supplied project
evidence.

Question:
{question}

Project evidence:
{context_text}

Rules:
- Answer only from the supplied evidence.
- Do not invent facts.
- If the evidence does not support an answer, say that the evidence is
  insufficient.
- Be concise and directly answer the question.
""".strip()

    return llm_client.generate(prompt)


def main() -> None:
    """Run RAGAS evaluation against the real retrieval pipeline."""
    settings = get_settings()
    cases = load_ragas_evaluation_cases(GOLDEN_DATA)

    pipeline, embedding_model = build_rag_pipeline()

    project_ids = sorted(
        {
            case.project_id
            for case in cases
        }
    )

    for project_id in project_ids:
        pipeline.index_project(project_id)

    llm_client = LLMClientFactory.create(settings)

    evaluator = RagasEvaluator(
        llm=RagasLLMAdapter(llm_client=llm_client),
        embedding_model=embedding_model,
    )

    runtime_cases = []

    for case in cases:
        project_id = case.project_id

        retrieval_results = pipeline.retrieve(
            query=case.question,
            project_id=project_id,
            limit=TOP_K,
        )

        contexts = [
            result.chunk.content
            for result in retrieval_results
        ]

        if not contexts:
            raise ValueError(
                f"No retrieval contexts found for case {case.case_id}"
            )

        answer = generate_answer(
            question=case.question,
            contexts=contexts,
            llm_client=llm_client,
        )

        runtime_cases.append(
            case.model_copy(
                update={
                    "answer": answer,
                    "contexts": contexts,
                },
            ),
        )

        print()
        print("=" * 80)
        print(f"CASE: {case.case_id}")
        print("=" * 80)
        print(f"Question: {case.question}")
        print()
        print("Retrieved contexts:")
        for index, context in enumerate(contexts, start=1):
            print(f"{index}. {context}")
        print()
        print(f"Generated answer: {answer}")

    results = asyncio.run(
        evaluator.evaluate(runtime_cases),
    )

    summary = evaluator.summarize(results)

    print()
    print("=" * 80)
    print("RAGAS EVALUATION")
    print("=" * 80)
    print(f"LLM provider          : {settings.llm_provider.value}")
    print(f"LLM model             : {settings.llm_model}")
    print(f"Evaluation cases      : {summary.total_cases}")
    print(f"Mean faithfulness     : {summary.mean_faithfulness:.4f}")
    print(f"Mean answer relevancy : {summary.mean_answer_relevancy:.4f}")

    print()
    print("CASE SCORES")
    print("=" * 80)

    for result in results:
        print(
            f"{result.case_id}: "
            f"faithfulness={result.faithfulness:.4f}, "
            f"answer_relevancy={result.answer_relevancy:.4f}"
        )


if __name__ == "__main__":
    main()