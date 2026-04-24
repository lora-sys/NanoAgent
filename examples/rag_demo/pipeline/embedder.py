"""Local embedding using sentence-transformers."""

from typing import Optional
from sentence_transformers import SentenceTransformer


def _resolve_cache_path(model: str) -> str:
    """Resolve HF model name to local cache path if cached, else return name."""
    try:
        from huggingface_hub import snapshot_download

        return snapshot_download(model, local_files_only=True)
    except Exception:
        return model


class LocalEmbedder:
    """Local embedding using sentence-transformers.

    Loads a model once, reuses across calls.
    """

    def __init__(self, model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize embedder and load model."""
        self.model = model
        self._client: Optional[SentenceTransformer] = None

    @property
    def client(self) -> SentenceTransformer:
        if self._client is None:
            local_path = _resolve_cache_path(self.model)
            self._client = SentenceTransformer(local_path)
        return self._client

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors (384-dim for all-MiniLM-L6-v2)
        """
        if not texts:
            return []
        emb = self.client.encode(texts, normalize_embeddings=True)
        return [row.tolist() for row in emb]

    def embed_one(self, text: str) -> list[float]:
        """Embed a single text.

        Args:
            text: Text string

        Returns:
            Embedding vector
        """
        return self.embed([text])[0]

    def dimension(self) -> int:
        """Return embedding dimension."""
        return self.client.get_embedding_dimension()
