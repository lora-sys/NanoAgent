"""RAG tools for NanoAgent integration.

rag_query: Query the RAG system for answers grounded in uploaded documents.
rag_ingest:  Ingest a file (or all project files) into the RAG system.
rag_status:  Check how many documents are indexed.
"""

import requests
from pathlib import Path
from typing import Any

from examples.rag_demo.config import RAG_SERVER

RAG_TIMEOUT = 30  # seconds


def rag_status() -> dict[str, Any]:
    """Check RAG system status: how many documents are indexed."""
    try:
        resp = requests.get(f"{RAG_SERVER}/files", timeout=5)
        if resp.status_code == 200:
            docs = resp.json().get("docs", [])
            return {
                "status": "ok",
                "document_count": len(docs),
                "documents": [d["filename"] for d in docs],
            }
        return {"status": "error", "message": f"HTTP {resp.status_code}"}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "RAG server not running at " + RAG_SERVER}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def rag_query(question: str, top_k: int = 5, min_score: float = 0.3) -> dict[str, Any]:
    """Query the RAG system for grounded answers.

    Returns a dict with:
    - answer: the generated answer (may say "未找到" if no relevant chunks)
    - citations: list of {index, file, line_start, line_end, score}
    - sources: raw chunks for display
    """
    try:
        resp = requests.post(
            f"{RAG_SERVER}/query",
            params={"question": question, "top_k": top_k, "min_score": min_score},
            timeout=RAG_TIMEOUT,
        )
        if resp.status_code == 200:
            return resp.json()
        return {"status": "error", "message": f"HTTP {resp.status_code}", "answer": ""}
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "message": f"RAG server not running at {RAG_SERVER}",
            "answer": "RAG server is not available. Start with: uv run python -m examples.rag_demo.server serve",
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "answer": ""}


def rag_ingest_file(filepath: str | Path) -> dict[str, Any]:
    """Ingest a single file into the RAG system."""
    try:
        with open(filepath, "rb") as f:
            resp = requests.post(
                f"{RAG_SERVER}/upload",
                files={"file": (Path(filepath).name, f, "text/plain")},
                timeout=RAG_TIMEOUT,
            )
        if resp.status_code == 200:
            return resp.json()
        return {"status": "error", "message": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def rag_reset() -> dict[str, Any]:
    """Reset RAG state (clear all documents). Use with caution."""
    try:
        resp = requests.post(f"{RAG_SERVER}/reset", timeout=5)
        if resp.status_code == 200:
            return {"status": "ok"}
        return {"status": "error", "message": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
