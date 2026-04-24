"""Document loader: extract text from .txt and .pdf files."""

from pathlib import Path


def load_document(path: str) -> str:
    """Load and extract text from a document.

    Args:
        path: Path to the document file (.txt or .pdf)

    Returns:
        Extracted text content

    Raises:
        ValueError: If file type is not supported
    """
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".txt":
        return _load_txt(p)
    elif suffix == ".pdf":
        return _load_pdf(p)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def _load_txt(p: Path) -> str:
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _load_pdf(p: Path) -> str:
    try:
        import pypdf

        reader = pypdf.PdfReader(str(p))
        parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
        return "\n".join(parts)
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {e}")
