"""ChromaDB vector store for RAG chunks."""

from pathlib import Path

import chromadb
from chromadb.config import Settings

from examples.rag_demo.config import CHROMA_COLLECTION, CHROMA_PERSIST_DIR
from examples.rag_demo.pipeline.chunker import Chunk


class ChromaStore:
    """ChromaDB store for RAG chunks with metadata."""

    def __init__(
        self,
        collection_name: str = CHROMA_COLLECTION,
        persist_dir: str = CHROMA_PERSIST_DIR,
        distance_metric: str = "cosine",
    ):
        self.persist_dir = persist_dir
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create collection
        try:
            self._collection = self._client.get_collection(name=collection_name)
        except Exception:
            self._collection = self._client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": distance_metric},
            )

    def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> int:
        """Add chunks with embeddings to the store.

        Args:
            chunks: List of Chunk objects
            embeddings: List of embedding vectors (same length as chunks)

        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0

        ids = [
            f"chunk_{i}_{chunks[i].metadata.get('file', 'unknown')}"
            for i in range(len(chunks))
        ]
        texts = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        return len(chunks)

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """Search for top-k most similar chunks.

        Args:
            query_embedding: Query vector
            top_k: Number of results

        Returns:
            List of result dicts: {text, distance, metadata}
        """
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        docs = results.get("documents", [[]])[0]
        dists = results.get("distances", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        return [
            {
                "text": doc,
                "distance": dist,
                "metadata": meta or {},
            }
            for doc, dist, meta in zip(docs, dists, metas)
        ]

    def delete_by_file(self, filename: str) -> None:
        """Delete all chunks from a given file.

        Args:
            filename: Name of the file to delete chunks for
        """
        # Get all IDs for this file
        all_data = self._collection.get(include=["metadatas"])
        ids = all_data.get("ids", [])
        metas = all_data.get("metadatas", [])

        to_delete = [
            tid
            for tid, meta in zip(ids, metas)
            if meta and meta.get("file") == filename
        ]

        if to_delete:
            self._collection.delete(ids=to_delete)

    def count(self) -> int:
        """Return total number of chunks."""
        return self._collection.count()

    def clear(self) -> None:
        """Delete all chunks."""
        self._client.delete_collection(name=self._collection.name)
        # Recreate
        self._collection = self._client.create_collection(
            name=self._collection.name,
            metadata={"hnsw:space": "cosine"},
        )
