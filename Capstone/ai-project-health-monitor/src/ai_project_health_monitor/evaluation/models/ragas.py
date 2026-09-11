from pydantic import BaseModel, Field


class RagasEvaluationCase(BaseModel):
    """Golden test case for RAGAS evaluation."""

    project_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    contexts: list[str] = Field(min_length=1)


class RagasEvaluationResult(BaseModel):
    """RAGAS evaluation result for a single case."""

    project_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    faithfulness: float = Field(ge=0.0, le=1.0)
    answer_relevancy: float = Field(ge=0.0, le=1.0)
    context_precision: float | None = Field(default=None, ge=0.0, le=1.0)
    context_recall: float | None = Field(default=None, ge=0.0, le=1.0)


class RagasEvaluationSummary(BaseModel):
    """Aggregated RAGAS evaluation metrics."""

    total_cases: int = Field(ge=0)
    mean_faithfulness: float = Field(ge=0.0, le=1.0)
    mean_answer_relevancy: float = Field(ge=0.0, le=1.0)
    mean_context_precision: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    mean_context_recall: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )