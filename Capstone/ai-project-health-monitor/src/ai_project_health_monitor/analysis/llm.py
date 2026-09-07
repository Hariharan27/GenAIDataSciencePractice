from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):
    """Contract for interacting with a large language model."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Generate a response from the language model."""
        raise NotImplementedError