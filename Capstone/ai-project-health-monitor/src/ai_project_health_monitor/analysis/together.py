from typing import Any

from together import Together

from ai_project_health_monitor.analysis.llm import LLMClient


class TogetherLLMClient(LLMClient):
    """LLM client implementation backed by Together."""

    def __init__(
        self,
        model: str,
        api_key: str,
    ) -> None:
        if not model.strip():
            raise ValueError("model must not be empty")

        if not api_key.strip():
            raise ValueError("api_key must not be empty")

        self._model = model
        self._client = Together(api_key=api_key)

    def generate(
        self,
        prompt: str,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Generate a response using the configured Together model."""
        if not prompt.strip():
            raise ValueError("prompt must not be empty")

        request: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        if response_format is not None:
            request["response_format"] = response_format

        response = self._client.chat.completions.create(
            **request,
        )
        
        print("\n========== TOGETHER RESPONSE ==========")
        print(response)
        print("========================================\n")

        choice = response.choices[0]
        message = choice.message

        if message is None:
            raise ValueError("Together response message must not be None")

        content = message.content

        if not isinstance(content, str):
            raise TypeError("Together response content must be a string")

        return content