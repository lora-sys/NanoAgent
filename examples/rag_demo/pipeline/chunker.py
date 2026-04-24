"""Recursive chunker: split text into overlapping chunks by paragraphs/sentences."""

import bisect
import re
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    metadata: dict  # {file: str, start_line: int, end_line: int}


_SENTENCE_END = re.compile(r"[.!?。！？]\s+")
_PARAGRAPH_BREAK = re.compile(r"\n{2,}")
_NEWLINE = re.compile(r"\n")


def recursive_chunk(
    text: str,
    chunk_size: int = 512,
    overlap: int = 100,
    filename: str = "unknown",
) -> list[Chunk]:
    """Split text into overlapping chunks using recursive strategy.

    Strategy:
    1. Split by paragraphs (double newlines)
    2. For each paragraph that fits in chunk_size → emit as chunk
    3. For oversized paragraphs → split by sentences, then by fixed chars
    4. Adjacent chunks overlap by `overlap` characters to preserve context

    Args:
        text: Cleaned text
        chunk_size: Max characters per chunk
        overlap: Characters of overlap between adjacent chunks
        filename: Source filename for metadata

    Returns:
        List of Chunk objects with text and metadata
    """
    # Track line numbers for metadata
    lines = text.split("\n")
    line_offsets = [0]
    for line in lines:
        line_offsets.append(line_offsets[-1] + len(line) + 1)

    def offset_to_line(pos: int) -> int:
        """Convert character offset to line number (O(log n) via bisect)."""
        idx = bisect.bisect_right(line_offsets, pos)
        return idx if idx > 0 else 1

    chunks = []
    paragraphs = [p.strip() for p in _PARAGRAPH_BREAK.split(text) if p.strip()]

    for para in paragraphs:
        if len(para) <= chunk_size:
            # Paragraph fits → emit as chunk
            start_line = offset_to_line(text.find(para))
            chunks.append(
                Chunk(
                    text=para,
                    metadata={
                        "file": filename,
                        "start_line": start_line,
                        "end_line": start_line + para.count("\n"),
                    },
                )
            )
        else:
            # Oversized → split by sentences then by chars
            chunks.extend(
                _split_oversized(
                    para, chunk_size, overlap, filename, text, offset_to_line
                )
            )

    # Add overlap between adjacent chunks
    return _add_overlap(chunks, overlap)


def _split_oversized(
    text: str,
    chunk_size: int,
    overlap: int,
    filename: str,
    full_text: str,
    offset_to_line,
) -> list[Chunk]:
    """Split oversized text by sentences then by fixed characters."""
    chunks = []

    # Try sentence boundaries first
    sentence_parts = _SENTENCE_END.split(text)
    current = ""

    for part in sentence_parts:
        if not part:
            continue
        sep = ". " if part.endswith(".") or part.endswith("。") else ""
        candidate = (current + sep + part).strip() if current else part

        if len(candidate) <= chunk_size:
            current = candidate
        else:
            # current is full enough → emit
            if current:
                start = full_text.find(current)
                chunks.append(
                    Chunk(
                        text=current,
                        metadata={
                            "file": filename,
                            "start_line": offset_to_line(start),
                            "end_line": offset_to_line(start + len(current)),
                        },
                    )
                )
            # Start new chunk with this part (may still be oversized)
            current = part

    if current:
        remaining = current
        while remaining:
            if len(remaining) <= chunk_size:
                start = full_text.find(remaining)
                if start == -1:
                    start = 0
                chunks.append(
                    Chunk(
                        text=remaining,
                        metadata={
                            "file": filename,
                            "start_line": offset_to_line(start),
                            "end_line": offset_to_line(start + len(remaining)),
                        },
                    )
                )
                break

            # Split by fixed size
            chunk_text = remaining[:chunk_size]
            start = full_text.find(chunk_text)
            if start == -1:
                start = 0
            chunks.append(
                Chunk(
                    text=chunk_text,
                    metadata={
                        "file": filename,
                        "start_line": offset_to_line(start),
                        "end_line": offset_to_line(start + len(chunk_text)),
                    },
                )
            )
            remaining = remaining[chunk_size - overlap :]
            if remaining and remaining == chunk_text:
                # Avoid infinite loop on single-char remaining
                break

    return chunks


def _find_sentence_boundary(text: str, max_chars: int) -> int:
    """Find the last sentence boundary within max_chars from end.

    Scans for sentence-ending punctuation (.!?。？) near the end of text.
    Returns the character index where the previous chunk's overlap should start.
    Falls back to max_chars if no sentence boundary is found within range.
    """
    search_start = max(0, len(text) - max_chars)
    # Find all sentence boundaries after search_start
    for match in reversed(list(_SENTENCE_END.finditer(text))):
        if match.start() >= search_start:
            # Return position right after the sentence-ending punctuation
            return match.end()
    return 0  # fallback: include from start of chunk


def _add_overlap(chunks: list[Chunk], overlap: int) -> list[Chunk]:
    """Add overlap text to consecutive chunks by prepending text from previous."""
    if overlap <= 0 or len(chunks) < 2:
        return chunks

    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_text = result[-1].text
        curr_text = chunks[i].text

        # Find a sentence boundary near the end of previous chunk for natural overlap
        boundary = _find_sentence_boundary(prev_text, overlap)
        prepend = prev_text[boundary:] if boundary > 0 else prev_text[-overlap:]
        if len(prepend) > overlap:
            prepend = prev_text[-overlap:]  # fallback to char-level if sentence too long
        new_text = prepend + curr_text
        new_meta = dict(chunks[i].metadata)
        new_meta["overlap_from_prev"] = True

        result.append(Chunk(text=new_text, metadata=new_meta))

    return result
