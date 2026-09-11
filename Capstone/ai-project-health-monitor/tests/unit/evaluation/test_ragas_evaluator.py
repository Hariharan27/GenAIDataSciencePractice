import pytest

from ai_project_health_monitor.evaluation.models.ragas import (
    RagasEvaluationCase,
    RagasEvaluationResult,
)
from ai_project_health_monitor.evaluation.ragas_evaluator import RagasEvaluator
from ai_project_health_monitor.rag.embeddings.base import EmbeddingModel


class FakeMetric:
    def __init__(self, score: float) -> None:
        self._score = score
        self.received_sample = None

    async def single_turn_ascore(self, sample) -> float:
        self.received_sample = sample
        return self._score


class FakeLLM:
    pass


class FakeEmbeddingModel(EmbeddingModel):
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


@pytest.mark.asyncio
async def test_evaluate_case_returns_ragas_scores() -> None:
    evaluator = RagasEvaluator(
        llm=FakeLLM(),
        embedding_model=FakeEmbeddingModel(),
    )

    evaluator._faithfulness = FakeMetric(0.9)
    evaluator._answer_relevancy = FakeMetric(0.8)

    case = RagasEvaluationCase(
        project_id="PROJ-001",
        case_id="RAGAS-001",
        question="What is blocking the payment integration?",
        answer="The payment API integration is blocked because credentials are unavailable.",
        contexts=[
            "Payment API integration is blocked because the external API team "
            "has not provided credentials.",
        ],
    )

    result = await evaluator.evaluate_case(case)

    assert result.case_id == "RAGAS-001"
    assert result.faithfulness == 0.9
    assert result.answer_relevancy == 0.8

    faithfulness_sample = evaluator._faithfulness.received_sample
    assert faithfulness_sample.user_input == case.question
    assert faithfulness_sample.response == case.answer
    assert faithfulness_sample.retrieved_contexts == case.contexts

@pytest.mark.asyncio
async def test_evaluate_returns_results_for_multiple_cases() -> None:
    evaluator = RagasEvaluator(
        llm=FakeLLM(),
        embedding_model=FakeEmbeddingModel(),
    )

    evaluator._faithfulness = FakeMetric(0.9)
    evaluator._answer_relevancy = FakeMetric(0.8)

    cases = [
        RagasEvaluationCase(
            project_id="PROJ-001",
            case_id="RAGAS-001",
            question="What is blocking the payment integration?",
            answer="The payment API integration is blocked.",
            contexts=["Payment API integration is blocked."],
        ),
        RagasEvaluationCase(
            project_id="PROJ-001",
            case_id="RAGAS-002",
            question="Are there scope changes?",
            answer="An additional dashboard was requested.",
            contexts=["An additional dashboard was requested."],
        ),
    ]

    results = await evaluator.evaluate(cases)

    assert len(results) == 2
    assert results[0].case_id == "RAGAS-001"
    assert results[0].faithfulness == 0.9
    assert results[1].case_id == "RAGAS-002"
    assert results[1].answer_relevancy == 0.8


@pytest.mark.asyncio
async def test_summarize_returns_mean_scores() -> None:
    evaluator = RagasEvaluator(
        llm=FakeLLM(),
        embedding_model=FakeEmbeddingModel(),
    )

    results = [
        RagasEvaluationResult(
            project_id="PROJ-001",
            case_id="RAGAS-001",
            faithfulness=0.9,
            answer_relevancy=0.8,
        ),
        RagasEvaluationResult(
            project_id="PROJ-001",
            case_id="RAGAS-002",
            faithfulness=0.7,
            answer_relevancy=1.0,
        ),
    ]

    summary = evaluator.summarize(results)

    assert summary.total_cases == 2
    assert summary.mean_faithfulness == 0.8
    assert summary.mean_answer_relevancy == 0.9
    