from typing import Any

from ollama import Client

from ai_project_health_monitor.analysis.llm import LLMClient


class OllamaLLMClient(LLMClient):
    """LLM client implementation backed by Ollama."""

    def __init__(
        self,
        model: str,
        host: str = "http://localhost:11434",
    ) -> None:
        if not model.strip():
            raise ValueError("model cannot be empty")

        if not host.strip():
            raise ValueError("host cannot be empty")

        self._model = model
        self._client = Client(host=host)

    def generate(
        self,
        prompt: str,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        if not prompt.strip():
            raise ValueError("prompt cannot be empty")

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
            request["format"] = self._to_ollama_format(response_format)

        response = self._client.chat(**request)

        content = response["message"]["content"]

        if not isinstance(content, str):
            raise TypeError("Ollama response content must be a string")

        return content

    @staticmethod
    def _to_ollama_format(
        response_format: dict[str, Any],
    ) -> dict[str, Any] | str:
        """Convert the provider-neutral response format to Ollama's format."""

        response_type = response_format.get("type")

        if response_type == "json_schema":
            json_schema = response_format.get("json_schema")

            if not isinstance(json_schema, dict):
                raise ValueError(
                    "json_schema response format must contain a json_schema object"
                )

            schema = json_schema.get("schema")

            if not isinstance(schema, dict):
                raise ValueError(
                    "json_schema response format must contain a schema object"
                )

            return schema

        if response_type == "json_object":
            return "json"

        raise ValueError(
            f"Unsupported response format type for Ollama: {response_type!r}"
        )