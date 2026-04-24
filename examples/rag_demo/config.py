"""RAG Demo configuration constants."""

import os

CHUNK_SIZE = 512  # characters per chunk
OVERLAP = 100  # overlap between chunks
TOP_K = 5  # top-k chunks to retrieve
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # local embedding
CHROMA_COLLECTION = "nanoagent_rag"
CHROMA_PERSIST_DIR = ".chromadb"
RAG_SERVER = os.getenv("RAG_SERVER", "http://localhost:8765")
