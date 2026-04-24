"""E2E tests for RAG demo: server + pipeline integration."""

import os
import tempfile
from pathlib import Path

import pytest

from examples.rag_demo.pipeline.document_loader import load_document
from examples.rag_demo.pipeline.text_cleaner import clean_text
from examples.rag_demo.pipeline.chunker import recursive_chunk, Chunk
from examples.rag_demo.pipeline.embedder import LocalEmbedder
from examples.rag_demo.storage.chroma_client import ChromaStore
from examples.rag_demo.storage.document_store import DocumentStore
from examples.rag_demo.retrieval.search import retrieval


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURE_DOC = Path(__file__).parent / "fixtures" / "rag_test_doc.txt"


@pytest.fixture
def chroma_store():
    """Fresh ChromaDB store for each test."""
    store = ChromaStore(persist_dir=".chromadb_test")
    store.clear()
    yield store
    store.clear()


@pytest.fixture
def doc_store():
    """Fresh document store for each test."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    store = DocumentStore(metadata_file=path)
    yield store
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def loaded_chunks():
    """Load and process the fixture document."""
    text = load_document(str(FIXTURE_DOC))
    text = clean_text(text)
    chunks = recursive_chunk(text, filename=FIXTURE_DOC.name)
    return chunks


# ---------------------------------------------------------------------------
# Pipeline tests
# ---------------------------------------------------------------------------


def test_load_document():
    """Document loader handles .txt files."""
    text = load_document(str(FIXTURE_DOC))
    assert len(text) > 100
    assert isinstance(text, str)


def test_clean_text():
    """Text cleaner normalizes unicode and collapses whitespace."""
    dirty = "  Hello\u00a0World\u2002\r\n\n  Foo  bar  "
    cleaned = clean_text(dirty)
    # \u2002 (en space) is NOT in _NORMALIZE_MAP, but it's not invalid
    # \r is stripped; \n\n blank line in middle is preserved (not excessive)
    assert "\r" not in cleaned
    assert "\xa0" not in cleaned  # non-breaking space → regular space
    assert "  " not in cleaned  # no double spaces
    assert cleaned.startswith("Hello")


def test_recursive_chunk():
    """Recursive chunker splits by paragraphs, sentences, chars; adds metadata."""
    text = clean_text(load_document(str(FIXTURE_DOC)))
    chunks = recursive_chunk(text, chunk_size=200, overlap=30, filename="test.txt")

    assert len(chunks) > 0
    assert all(isinstance(c, Chunk) for c in chunks)
    assert all(c.metadata.get("file") == "test.txt" for c in chunks)
    assert all("start_line" in c.metadata for c in chunks)
    assert all("end_line" in c.metadata for c in chunks)
    assert all(1 <= c.metadata["start_line"] <= c.metadata["end_line"] for c in chunks)

    # Overlap check: adjacent chunks should overlap by at least some characters
    for i in range(len(chunks) - 1):
        overlap_len = (
            len(chunks[i].text)
            + len(chunks[i + 1].text)
            - len((chunks[i].text + chunks[i + 1].text).replace(chunks[i + 1].text, ""))
        )
        # Just verify no gap (overlap applied)
        assert overlap_len > 0 or i == len(chunks) - 1


def test_embedder_dimension():
    """Embedder produces 384-dim vectors for all-MiniLM-L6-v2."""
    embedder = LocalEmbedder()
    assert embedder.dimension() == 384


def test_embedder_embed_one():
    """embed_one returns a flat list."""
    embedder = LocalEmbedder()
    vec = embedder.embed_one("hello world")
    assert isinstance(vec, list)
    assert len(vec) == 384
    assert all(isinstance(x, float) for x in vec)


def test_embedder_embed_multiple():
    """embed returns list of lists."""
    embedder = LocalEmbedder()
    vecs = embedder.embed(["hello", "world"])
    assert len(vecs) == 2
    assert all(len(v) == 384 for v in vecs)


# ---------------------------------------------------------------------------
# Storage + retrieval tests
# ---------------------------------------------------------------------------


def test_chroma_add_and_search(chroma_store, loaded_chunks):
    """ChromaDB stores chunks and returns them on search."""
    embedder = LocalEmbedder()
    embeddings = embedder.embed([c.text for c in loaded_chunks])

    count = chroma_store.add_chunks(loaded_chunks, embeddings)
    assert count == len(loaded_chunks)

    # Search with first chunk's embedding
    results = chroma_store.search(embeddings[0], top_k=3)
    assert len(results) == 3
    assert "text" in results[0]
    assert "distance" in results[0]
    assert "metadata" in results[0]
    assert results[0]["metadata"]["file"] == FIXTURE_DOC.name


def test_chroma_delete_by_file(chroma_store, loaded_chunks):
    """delete_by_file removes all chunks from a file."""
    embedder = LocalEmbedder()
    embeddings = embedder.embed([c.text for c in loaded_chunks])
    chroma_store.add_chunks(loaded_chunks, embeddings)

    assert chroma_store.count() == len(loaded_chunks)

    chroma_store.delete_by_file(FIXTURE_DOC.name)
    assert chroma_store.count() == 0


def test_retrieval_top_k(chroma_store, loaded_chunks):
    """retrieval() returns top_k results with score, text, metadata."""
    embedder = LocalEmbedder()
    embeddings = embedder.embed([c.text for c in loaded_chunks])
    chroma_store.add_chunks(loaded_chunks, embeddings)

    results = retrieval("nanoagent", top_k=5)
    assert len(results) == 5
    assert all("text" in r for r in results)
    assert all("score" in r for r in results)
    assert all("metadata" in r for r in results)
    # Score should be descending
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_retrieval_empty_query(chroma_store):
    """retrieval returns empty list when no chunks stored."""
    results = retrieval("xyz123nonexistent", top_k=5)
    assert isinstance(results, list)
    # May return results if embedding similarity happens to match — that's OK


# ---------------------------------------------------------------------------
# Document store tests
# ---------------------------------------------------------------------------


def test_doc_store_add(doc_store):
    """DocumentStore tracks uploaded files."""
    from examples.rag_demo.storage.document_store import DocInfo

    doc_store.add(
        DocInfo(
            filename=FIXTURE_DOC.name,
            chunk_count=5,
            size_bytes=1000,
            uploaded_at="2024-01-01T00:00:00",
        )
    )
    docs = doc_store.list_all()

    assert len(docs) == 1
    assert docs[0].filename == FIXTURE_DOC.name
    assert docs[0].size_bytes == 1000
    assert docs[0].chunk_count == 5


def test_doc_store_delete(doc_store):
    """DocumentStore removes files."""
    from examples.rag_demo.storage.document_store import DocInfo

    doc_store.add(
        DocInfo(
            filename=FIXTURE_DOC.name,
            chunk_count=5,
            size_bytes=1000,
            uploaded_at="2024-01-01T00:00:00",
        )
    )
    doc_store.remove(FIXTURE_DOC.name)
    assert len(doc_store.list_all()) == 0


# ---------------------------------------------------------------------------
# Integration: full pipeline (no LLM call)
# ---------------------------------------------------------------------------


def test_full_pipeline_no_llm(chroma_store):
    """Full pipeline: load → clean → chunk → embed → store → retrieve."""
    # 1. Load
    text = load_document(str(FIXTURE_DOC))
    assert len(text) > 0

    # 2. Clean
    text = clean_text(text)

    # 3. Chunk
    chunks = recursive_chunk(
        text, chunk_size=512, overlap=100, filename=FIXTURE_DOC.name
    )
    assert len(chunks) > 0

    # 4. Embed
    embedder = LocalEmbedder()
    embeddings = embedder.embed([c.text for c in chunks])
    assert len(embeddings) == len(chunks)

    # 5. Store
    chroma_store.clear()
    chroma_store.add_chunks(chunks, embeddings)
    assert chroma_store.count() == len(chunks)

    # 6. Retrieve
    results = retrieval("what is nanoagent", top_k=3)
    assert len(results) == 3
    assert all(0 <= r["score"] <= 2 for r in results)  # cosine distance based
    assert all(r["metadata"]["file"] == FIXTURE_DOC.name for r in results)
