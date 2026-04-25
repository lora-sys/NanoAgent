"""In-memory store — ephemeral, dict-based."""

from typing import Any, Dict, List, Optional

from core.memory.interfaces import BaseMemory, MemoryStats


class InMemoryStore(BaseMemory):
    """
    Dict-based ephemeral store for short-term and working memory.
    Not persistent across processes.
    """

    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._access_count: Dict[str, int] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str, default: Any = None) -> Any:
        val = self._store.get(key)
        if val is not None:
            self._hits += 1
            self._access_count[key] = self._access_count.get(key, 0) + 1
        else:
            self._misses += 1
        return val if val is not None else default

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value
        self._access_count[key] = self._access_count.get(key, 0) + 1

    def delete(self, key: str) -> None:
        self._store.pop(key, None)
        self._access_count.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
        self._access_count.clear()

    def to_context_string(self, max_tokens: int = 1000) -> str:
        """Serialize store to context string with token budget."""
        if not self._store:
            return ""

        # Rough token estimation: ~4 chars per token
        budget_chars = max_tokens * 4
        parts = []
        current_len = 0

        # Sort by access count (most used first)
        sorted_items = sorted(
            self._store.items(),
            key=lambda x: self._access_count.get(x[0], 0),
            reverse=True
        )

        for key, value in sorted_items:
            entry = f"{key}: {value}"
            entry_len = len(entry)
            if current_len + entry_len + 2 <= budget_chars:
                parts.append(entry)
                current_len += entry_len + 2
            else:
                break

        return "\n".join(parts)

    @property
    def memory_type(self) -> str:
        return "in_memory"

    @property
    def stats(self) -> MemoryStats:
        return MemoryStats(hits=self._hits, misses=self._misses)


class WorkingMemoryStore(InMemoryStore):
    """Working memory with tool result tracking."""

    def __init__(self):
        super().__init__()
        self._tool_results: List[Dict[str, Any]] = []

    def add_tool_result(self, tool_name: str, result: Any) -> None:
        """Record tool execution result."""
        self._tool_results.append({
            "tool": tool_name,
            "result": result,
            "ts": len(self._tool_results)
        })
        # Keep last 10 results
        if len(self._tool_results) > 10:
            self._tool_results = self._tool_results[-10:]

    def get_recent_results(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get n most recent tool results."""
        return self._tool_results[-n:]

    @property
    def memory_type(self) -> str:
        return "working"