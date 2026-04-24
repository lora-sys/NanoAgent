"""Document metadata store: track uploaded files and their chunks."""

from dataclasses import dataclass
from pathlib import Path
import json

_METADATA_FILE = ".rag_docs.json"


@dataclass
class DocInfo:
    filename: str
    chunk_count: int
    size_bytes: int
    uploaded_at: str  # ISO timestamp


class DocumentStore:
    """Track metadata of uploaded RAG documents."""

    def __init__(self, metadata_file: str = _METADATA_FILE):
        self.metadata_file = metadata_file
        self._docs: dict[str, DocInfo] = {}
        self._load()

    def _load(self) -> None:
        p = Path(self.metadata_file)
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                self._docs = {k: DocInfo(**v) for k, v in data.items()}
            except Exception:
                pass

    def _save(self) -> None:
        data = {k: vars(v) for k, v in self._docs.items()}
        Path(self.metadata_file).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add(self, doc: DocInfo) -> None:
        self._docs[doc.filename] = doc
        self._save()

    def remove(self, filename: str) -> bool:
        if filename in self._docs:
            del self._docs[filename]
            self._save()
            return True
        return False

    def get(self, filename: str) -> DocInfo | None:
        return self._docs.get(filename)

    def list_all(self) -> list[DocInfo]:
        return list(self._docs.values())

    def exists(self, filename: str) -> bool:
        return filename in self._docs

    def clear(self) -> None:
        """Clear all documents from the store."""
        self._docs.clear()
        self._save()
