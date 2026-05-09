"""Simple HTTP server for RAG demo.

Endpoints:
    POST /upload          — upload a .txt or .pdf file
    GET  /files           — list uploaded documents
    DELETE /files/<filename> — delete a document
    POST /query           — query the RAG system
    GET  /               — serve frontend
"""

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from examples.rag_demo.pipeline.chunker import recursive_chunk
from examples.rag_demo.pipeline.document_loader import load_document
from examples.rag_demo.pipeline.embedder import LocalEmbedder
from examples.rag_demo.pipeline.text_cleaner import clean_text
from examples.rag_demo.storage.chroma_client import ChromaStore
from examples.rag_demo.storage.document_store import DocInfo, DocumentStore

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB upload limit

app = FastAPI()

# CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
_store: Optional[DocumentStore] = None
_chroma: Optional[ChromaStore] = None
_embedder: Optional[LocalEmbedder] = None

APP_DIR = Path(__file__).parent
FRONTEND_DIR = APP_DIR / "frontend"


def get_store() -> DocumentStore:
    global _store
    if _store is None:
        _store = DocumentStore()
    return _store


def get_chroma() -> ChromaStore:
    global _chroma
    if _chroma is None:
        _chroma = ChromaStore()
    return _chroma


def get_embedder() -> LocalEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = LocalEmbedder()
    return _embedder


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """Upload a .txt or .pdf file, process it, and store in ChromaDB."""
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    filename = Path(file.filename).name
    suffix = Path(filename).suffix.lower()
    if suffix not in (".txt", ".pdf"):
        raise HTTPException(400, f"Unsupported file type: {suffix}")

    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                413,
                f"File too large: {len(content) / 1024:.0f} KB > {MAX_FILE_SIZE / 1024:.0f} KB",
            )
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Load and clean
        text = load_document(tmp_path)
        text = clean_text(text)

        if not text.strip():
            raise HTTPException(400, "Document is empty after cleaning")

        # Chunk
        chunks = recursive_chunk(text, filename=filename)
        if not chunks:
            raise HTTPException(400, "Failed to chunk document")

        # Embed
        embedder = get_embedder()
        texts = [c.text for c in chunks]
        embeddings = embedder.embed(texts)

        # Store in ChromaDB
        chroma = get_chroma()
        chroma.add_chunks(chunks, embeddings)

        # Track metadata
        doc_info = DocInfo(
            filename=filename,
            chunk_count=len(chunks),
            size_bytes=len(content),
            uploaded_at=datetime.now(timezone.utc).isoformat(),
        )
        get_store().add(doc_info)

        return {
            "filename": filename,
            "chunks": len(chunks),
            "status": "ok",
        }
    finally:
        os.unlink(tmp_path)


@app.get("/files")
async def list_docs():
    """List all uploaded documents."""
    docs = get_store().list_all()
    return {
        "docs": [
            {
                "filename": d.filename,
                "chunk_count": d.chunk_count,
                "size_bytes": d.size_bytes,
                "uploaded_at": d.uploaded_at,
            }
            for d in docs
        ]
    }


@app.delete("/files/{filename}")
async def delete_doc(filename: str):
    """Delete a document and its chunks."""
    store = get_store()
    if not store.exists(filename):
        raise HTTPException(404, f"Document not found: {filename}")

    get_chroma().delete_by_file(filename)
    store.remove(filename)
    return {"filename": filename, "status": "deleted"}


@app.post("/reset")
async def reset_state():
    """Clear all ChromaDB chunks and document store. Use before eval for clean state."""
    get_chroma().clear()
    get_store().clear()
    from examples.rag_demo.retrieval.search import clear_cache

    clear_cache()
    return {"status": "reset"}


@app.post("/query")
async def query(
    question: str = Query(...),
    top_k: int = Query(default=5, le=20),
    min_score: float = Query(default=0.3, ge=0.0, le=2.0),
):
    """Query the RAG system."""
    if not question.strip():
        raise HTTPException(400, "Empty question")

    from examples.rag_demo.retrieval.search import retrieval

    chunks = retrieval(query=question, top_k=top_k, min_score=min_score)
    if not chunks:
        return {
            "answer": "未找到相关内容。请尝试不同的查询。",
            "citations": [],
            "sources": [],
        }

    from examples.rag_demo.generation.rag_chain import generate_with_citations

    result = generate_with_citations(query=question, top_k=top_k, chunks=chunks)

    return {
        "answer": result.answer,
        "citations": [
            {
                "index": c.index,
                "file": c.file,
                "line_start": c.line_start,
                "line_end": c.line_end,
                "score": c.score,
                "text_preview": c.text_preview,
            }
            for c in result.citations
        ],
        "sources": result.sources,
    }


@app.get("/")
async def root():
    """Serve the frontend."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    raise HTTPException(
        404, "Frontend not found. Run from examples/rag_demo/ directory."
    )


def run_server(host: str = "127.0.0.1", port: int = 8765):
    """Run the HTTP server."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)


cli = typer.Typer()


@cli.command()
def serve(host: str = "127.0.0.1", port: int = 8765):
    """Start the RAG demo server."""
    run_server(host=host, port=port)


@cli.command()
def ingest(filename: str, chunk_size: int = 512, overlap: int = 100):
    """Ingest a single file (command-line utility)."""
    text = load_document(filename)
    text = clean_text(text)
    chunks = recursive_chunk(text, filename=Path(filename).name)
    embedder = LocalEmbedder()
    embeddings = embedder.embed([c.text for c in chunks])
    chroma = get_chroma()
    n = chroma.add_chunks(chunks, embeddings)
    print(f"Ingested {n} chunks from {filename}")


if __name__ == "__main__":
    cli()
