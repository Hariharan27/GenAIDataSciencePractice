from collections.abc import Sequence

from ragas.dataset_schema import SingleTurnSample
from ragas.metrics._answer_relevance import AnswerRelevancy
from ragas.metrics._faithfulness import Faithfulness

from ai_project_health_monitor.analysis.llm import LLMClient
from ai_project_health_monitor.evaluation.models.ragas import (
    RagasEvaluationCase,
    RagasEvaluationResult,
    RagasEvaluationSummary,
)
from ai_project_health_monitor.evaluation.ragas_embeddings import RagasEmbeddingAdapter
from ai_project_health_monitor.evaluation.ragas_llm import RagasLLMAdapter
from ai_project_health_monitor.rag.embeddings.base import EmbeddingModel


class RagasEvaluator:
    """Evaluate generated RAG answers using RAGAS metrics."""

    def __init__(
        self,
        llm: LLMClient,
        embedding_model: EmbeddingModel,
    ) -> None:
        ragas_llm = RagasLLMAdapter(llm_client=llm)
        ragas_embeddings = RagasEmbeddingAdapter(
            embedding_model=embedding_model,
        )
        self._faithfulness = Faithfulness(llm=ragas_llm)
        self._answer_relevancy = AnswerRelevancy(
            llm=ragas_llm,
            embeddings=ragas_embeddings,
        )

    async def evaluate_case(
        self,
        case: RagasEvaluationCase,
    ) -> RagasEvaluationResult:
        """Evaluate one RAG answer."""
        sample = SingleTurnSample(
            user_input=case.question,
            retrieved_contexts=case.contexts,
            response=case.answer,
        )

        faithfulness = await self._faithfulness.single_turn_ascore(
            sample,
        )
        answer_relevancy = await self._answer_relevancy.single_turn_ascore(
            sample,
        )

        return RagasEvaluationResult(
            project_id=case.project_id,
            case_id=case.case_id,
            faithfulness=faithfulness,
            answer_relevancy=answer_relevancy,
        )

    async def evaluate(
        self,
        cases: Sequence[RagasEvaluationCase],
    ) -> list[RagasEvaluationResult]:
        """Evaluate multiple RAGAS cases."""
        results: list[RagasEvaluationResult] = []

        for case in cases:
            results.append(
                await self.evaluate_case(case),
            )

        return results

    def summarize(
        self,
        results: Sequence[RagasEvaluationResult],
    ) -> RagasEvaluationSummary:
        """Aggregate individual RAGAS results into summary metrics."""
        if not results:
            raise ValueError("RAGAS evaluation results cannot be empty")

        def mean(values: list[float]) -> float:
            return sum(values) / len(values)

        faithfulness_scores = [
            result.faithfulness
            for result in results
        ]
        answer_relevancy_scores = [
            result.answer_relevancy
            for result in results
        ]
        context_precision_scores = [
            result.context_precision
            for result in results
            if result.context_precision is not None
        ]
        context_recall_scores = [
            result.context_recall
            for result in results
            if result.context_recall is not None
        ]

        return RagasEvaluationSummary(
            total_cases=len(results),
            mean_faithfulness=mean(faithfulness_scores),
            mean_answer_relevancy=mean(answer_relevancy_scores),
            mean_context_precision=(
                mean(context_precision_scores)
                if context_precision_scores
                else None
            ),
            mean_context_recall=(
                mean(context_recall_scores)
                if context_recall_scores
                else None
            ),
        )