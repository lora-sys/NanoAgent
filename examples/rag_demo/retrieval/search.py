"""Vector retrieval: embed query, search ChromaDB, return ranked results.

Features:
- Query embedding cache (TTL 5min, thread-safe)
- Minimum score threshold filtering
- MMR-like deduplication (adjacent near-duplicate chunks filtered)
- ChromaStore singleton (one client instance per process)
"""

import threading
import time
from typing import Optional

from examples.rag_demo.config import TOP_K
from examples.rag_demo.pipeline.embedder import LocalEmbedder
from examples.rag_demo.storage.chroma_client import ChromaStore

# Default minimum similarity score (0-2 cosine distance scale, converted to 0-1 similarity)
# 0.3 threshold means chunks must be at least 30% similar
DEFAULT_MIN_SCORE = 0.3

# Query embedding cache: query_lower → (timestamp, results)
_QUERY_CACHE: dict[str, tuple[float, list[dict]]] = {}
_CACHE_LOCK = threading.Lock()

# Embedder singleton (lazy-loaded, shared across calls)
_embedder: Optional[LocalEmbedder] = None


def _get_embedder() -> LocalEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = LocalEmbedder()
    return _embedder


# ChromaStore singleton (lazy-loaded, shared across calls)
_chroma_store: Optional[ChromaStore] = None


def _get_chroma() -> ChromaStore:
    global _chroma_store
    if _chroma_store is None:
        _chroma_store = ChromaStore()
    return _chroma_store



def retrieval(
    query: str,
    top_k: int = TOP_K,
    min_score: float = DEFAULT_MIN_SCORE,
    cache_ttl: int = 300,
) -> list[dict]:
    """Embed query, search ChromaDB, return ranked chunks with citations.

    Args:
        query: User query string
        top_k: Number of chunks to retrieve
        min_score: Minimum similarity score (0-1) to include a chunk.
                   Below this threshold the chunk is dropped.
        cache_ttl: Query cache TTL in seconds (default 5min).

    Returns:
        List of result dicts:
        {
            "text": str,        # chunk text
            "score": float,     # similarity score (higher = more relevant)
            "metadata": dict    # {file, start_line, end_line}
        }
    """
    cache_key = query.strip().lower()

    # Thread-safe cache access
    with _CACHE_LOCK:
        if cache_key in _QUERY_CACHE:
            ts, cached = _QUERY_CACHE[cache_key]
            if time.time() - ts < cache_ttl:
                return cached[:top_k]

    embedder = _get_embedder()
    store = _get_chroma()

    query_emb = embedder.embed_one(query)
    raw_results = store.search(query_emb, top_k=top_k * 3)  # over-fetch for dedup

    # Convert distance to similarity score
    scored = []
    for r in raw_results:
        score = 1 - r["distance"]  # cosine distance → similarity
        scored.append({
            "text": r["text"],
            "score": round(score, 4),
            "metadata": r["metadata"],
        })

    # Sort by score descending
    scored.sort(key=lambda x: -x["score"])

    # ── Hallucination control: minimum score threshold ──────────────────────
    scored = [r for r in scored if r["score"] >= min_score]

    # ── MMR-like deduplication ─────────────────────────────────────────────────
    # Skip per-chunk embedding (too slow). Simple: deduplicate by start_line
    # within the same file — adjacent chunks from same paragraph get same line.
    seen_lines: set[tuple[str, int]] = set()
    filtered: list[dict] = []
    for r in scored:
        if len(filtered) >= top_k:
            break
        key = (r["metadata"].get("file", ""), r["metadata"].get("start_line", 0))
        if key not in seen_lines:
            filtered.append(r)
            seen_lines.add(key)

    # ── No results after filtering → return empty (triggers "未找到") ────────
    if not filtered:
        with _CACHE_LOCK:
            _QUERY_CACHE[cache_key] = (time.time(), [])
        return []

    # Cache the filtered results (thread-safe)
    with _CACHE_LOCK:
        _QUERY_CACHE[cache_key] = (time.time(), filtered)
    return filtered


def clear_cache() -> None:
    """Clear the query embedding cache."""
    _QUERY_CACHE.clear()
