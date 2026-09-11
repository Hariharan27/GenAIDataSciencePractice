from collections.abc import Sequence
from typing import Any

from langchain_core.outputs import Generation, LLMResult
from langchain_core.prompt_values import PromptValue
from ragas.llms.base import BaseRagasLLM
from ragas.run_config import RunConfig

from ai_project_health_monitor.analysis.llm import LLMClient


class RagasLLMAdapter(BaseRagasLLM):
    """Adapt the application's LLMClient to the RAGAS LLM interface."""

    def __init__(
        self,
        llm_client: LLMClient,
        run_config: RunConfig | None = None,
    ) -> None:
        super().__init__(run_config=run_config or RunConfig())
        self._llm_client = llm_client

    def generate_text(
    self,
    prompt: PromptValue,
    n: int = 1,
    temperature: float = 0.01,
    stop: Sequence[str] | None = None,
    callbacks: Any = None,
    ) -> LLMResult:
        del temperature, stop, callbacks

        prompt_text = prompt.to_string()

        generations = [
            Generation(
                text=self._llm_client.generate(prompt_text),
            )
            for _ in range(n)
        ]

        return LLMResult(generations=[generations])

    def is_finished(self, response: LLMResult) -> bool:
        """Return whether the RAGAS LLM response contains generations."""
        return bool(response.generations)

    async def agenerate_text(
        self,
        prompt: PromptValue,
        n: int = 1,
        temperature: float | None = 0.01,
        stop: Sequence[str] | None = None,
        callbacks: Any = None,
    ) -> LLMResult:
        del temperature, stop, callbacks

        prompt_text = prompt.to_string()

        generations = [
            Generation(
                text=self._llm_client.generate(prompt_text),
            )
            for _ in range(n)
        ]

        return LLMResult(generations=[generations])