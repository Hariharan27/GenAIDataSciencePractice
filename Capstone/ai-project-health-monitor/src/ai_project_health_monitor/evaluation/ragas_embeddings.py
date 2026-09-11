from typing import Any

from ragas.embeddings.base import BaseRagasEmbedding

from ai_project_health_monitor.rag.embeddings.base import EmbeddingModel


class RagasEmbeddingAdapter(BaseRagasEmbedding):
    """Adapt the application's embedding model to the RAGAS interface."""

    def __init__(self, embedding_model: EmbeddingModel) -> None:
        super().__init__()
        self._embedding_model = embedding_model

    def embed_text(
        self,
        text: str,
        **kwargs: Any,
    ) -> list[float]:
        """Generate one embedding using the application embedding model."""
        del kwargs

        embeddings = self._embedding_model.embed([text])

        if not embeddings:
            raise ValueError("embedding model returned no embedding")

        return embeddings[0]

    def embed_query(self, text: str) -> list[float]:
        """Generate one query embedding using the application embedding model."""
        return self.embed_text(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple documents."""
        return self._embedding_model.embed(texts)

    async def aembed_query(self, text: str) -> list[float]:
        """Generate one query embedding asynchronously."""
        return await self.aembed_text(text)

    async def aembed_text(
        self,
        text: str,
        **kwargs: Any,
    ) -> list[float]:
        """Generate one embedding asynchronously."""
        del kwargs

        return self.embed_text(text)