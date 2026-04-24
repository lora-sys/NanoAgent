"""RAG generation with full citation tracing.

Builds a prompt with retrieved chunks + citations, calls LLM,
returns answer and citation list for frontend display.

Anti-hallucination measures:
- Strengthened system prompt with mandatory source-grounding rules
- Citation validity check: removes [N] markers that don't correspond to real citations
- Minimum score threshold on retrieval (via search.py)
"""

import os
import re
from dataclasses import dataclass
from typing import Any

from examples.rag_demo.retrieval.search import retrieval


# Load model from nanoagent.toml
def _get_default_model() -> str:
    """Load LLM model from nanoagent.toml."""
    try:
        import toml

        path = os.environ.get("NANOAGENT_CONFIG", "nanoagent.toml")
        config = toml.load(path)
        return config.get("llm", {}).get("model", "openai/glm-4.6v")
    except Exception:
        return "openai/glm-4.6v"


@dataclass
class Citation:
    index: int  # 1-based citation number
    file: str  # source filename
    line_start: int  # start line
    line_end: int  # end line
    score: float  # similarity score
    text_preview: str  # first 100 chars of chunk


@dataclass
class RAGAnswer:
    answer: str
    citations: list[Citation]
    sources: list[dict]  # raw chunks for frontend display


_SYSTEM_PROMPT = """你是一个严格基于文档的问答助手。

## 核心规则
1. **只使用参考资料中的信息回答**。不要编造任何参考资料中没有的细节、数字、名称或结论。
2. **每个具体事实必须标注 [N] 来源**（如：[1] 或 [2][3]）。未标注的事实视为未经证实的猜测。
3. **如果问题无法从参考资料中完整回答**：只回答能回答的部分，然后明确说明"关于 [未知部分]，我目前掌握的资料中没有相关信息"。
4. **绝对禁止**：在没有参考资料支持的情况下给出肯定性断言（如"根据资料，X 一定 Y"）。
5. **引用格式**：使用 [N] 在句尾标注，每个 [N] 必须对应一个有效的参考资料编号。

## 参考资料
{chunks}

## 问题
{question}

## 回答（必须遵循上述规则）"""


def _build_citations_text(chunks: list[dict]) -> str:
    """Format chunks into citation block for prompt."""
    lines = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        preview = chunk["text"][:120].replace("\n", " ")
        lines.append(
            f"[{i}] file:{meta.get('file', '?')}:{meta.get('start_line', '?')} | "
            f"score:{chunk.get('score', 0):.3f}\n    {preview}…"
        )
    return "\n".join(lines)


def _format_sources(chunks: list[dict]) -> list[dict]:
    """Format chunks for frontend JSON response."""
    return [
        {
            "text": c["text"],
            "score": c["score"],
            "file": c["metadata"].get("file", ""),
            "line_start": c["metadata"].get("start_line", 0),
            "line_end": c["metadata"].get("end_line", 0),
        }
        for c in chunks
    ]


def generate_with_citations(
    query: str,
    top_k: int = 5,
    llm_client: Any = None,
    chunks: list[dict] | None = None,
) -> RAGAnswer:
    """Retrieve relevant chunks and generate answer with citations.

    Args:
        query: User question
        top_k: Number of chunks to retrieve
        llm_client: NanoLLMClient instance (optional, falls back to litellm direct)
        chunks: Optional pre-fetched chunks (from server which applies min_score).
                If None, retrieval() is called internally with DEFAULT_MIN_SCORE.

    Returns:
        RAGAnswer with answer text, Citation list, and raw sources
    """
    if chunks is None:
        chunks = retrieval(query, top_k=top_k)

    if not chunks:
        return RAGAnswer(
            answer="未找到相关内容。请尝试不同的查询。",
            citations=[],
            sources=[],
        )

    # Build citations list
    citations = [
        Citation(
            index=i + 1,
            file=c["metadata"].get("file", ""),
            line_start=c["metadata"].get("start_line", 0),
            line_end=c["metadata"].get("end_line", 0),
            score=c["score"],
            text_preview=c["text"][:100].replace("\n", " "),
        )
        for i, c in enumerate(chunks)
    ]

    # Build prompt
    chunks_text = _build_citations_text(chunks)
    prompt = _SYSTEM_PROMPT.format(chunks=chunks_text, question=query)

    # Call LLM
    if llm_client is not None:
        response = llm_client.chat([{"role": "user", "content": prompt}])
    else:
        import litellm

        response = litellm.completion(
            model=_get_default_model(),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        response = response.choices[0].message.content or ""

    # ── Citation validity check: remove [N] markers for invalid indices ─────────
    answer = _sanitize_citations(response, citations)

    return RAGAnswer(
        answer=answer,
        citations=citations,
        sources=_format_sources(chunks),
    )


def _sanitize_citations(answer: str, citations: list[Citation]) -> str:
    """Remove [N] markers that don't correspond to a valid citation index.

    Hallucination guard: if LLM cites [7] but only 3 chunks were retrieved,
    [7] → [?] to avoid misleading the user.
    """
    if not citations:
        return answer
    valid = set(c.index for c in citations)

    def replacer(m: re.Match) -> str:
        idx = int(m.group(1))
        return f"[{idx}]" if idx in valid else "[?]"

    return re.sub(r"\[(\d+)\]", replacer, answer)
