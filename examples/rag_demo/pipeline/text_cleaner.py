"""Text cleaner: normalize and clean extracted text."""

import re
import unicodedata


# Unicode categories to remove
_INVALID_CATEGORIES = {
    "Co",  # Private use area
    "Cs",  # Surrogate
    "Cn",  # Unassigned
}
# Characters to normalize to ASCII equivalents
_NORMALIZE_MAP = {
    "\u2018": "'",  # '
    "\u2019": "'",  # '
    "\u201c": '"',  # "
    "\u201d": '"',  # "
    "\u2013": "-",  # –
    "\u2014": "-",  # —
    "\xa0": " ",  # non-breaking space
    "\u2002": " ",  # en space
    "\u3000": " ",  # ideographic space
}


def clean_text(text: str) -> str:
    """Clean and normalize text.

    - Normalize unicode (NFKC)
    - Replace unicode punctuation with ASCII equivalents
    - Collapse multiple spaces/newlines to single
    - Strip leading/trailing whitespace
    - Remove lines with only whitespace

    Args:
        text: Raw text from document loader

    Returns:
        Cleaned text
    """
    # Normalize unicode
    text = unicodedata.normalize("NFKC", text)

    # Replace known unicode chars
    for old, new in _NORMALIZE_MAP.items():
        text = text.replace(old, new)

    # Remove invalid unicode categories
    text = "".join(
        c for c in text if unicodedata.category(c) not in _INVALID_CATEGORIES
    )

    # Collapse excessive whitespace
    text = re.sub(r"[ \t]+", " ", text)  # multiple spaces/tabs
    text = re.sub(r"\n{3,}", "\n\n", text)  # excessive newlines
    text = re.sub(r"^\s+$", "", text, flags=re.MULTILINE)  # blank lines

    # Remove non-printable chars (keep newlines and tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Normalize CRLF → LF, then strip standalone CR
    text = text.replace("\r\n", "\n").replace("\r", "")

    return text.strip()
