"""Memory optimizer — token budget management."""

from typing import Dict, List, Tuple


class MemoryOptimizer:
    """
    Token budget management for memory context.
    Tracks token usage per memory type and optimizes context string generation.
    """

    # Default token budgets per memory type
    DEFAULT_BUDGETS: Dict[str, int] = {
        "preference": 200,
        "cross_session": 400,
        "long_term": 500,
        "working": 300,
        "short_term": 100,
    }

    def __init__(self, budgets: Dict[str, int] | None = None):
        self._budgets = budgets or self.DEFAULT_BUDGETS.copy()
        self._usage: Dict[str, int] = {k: 0 for k in self._budgets}

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation: ~4 chars per token."""
        return len(text) // 4

    def truncate_to_budget(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token budget."""
        budget_chars = max_tokens * 4
        if len(text) <= budget_chars:
            return text
        return text[:budget_chars] + "..."

    def build_context(
        self,
        memory_contents: Dict[str, str],
        total_budget: int = 2000
    ) -> str:
        """
        Build context string from multiple memory sources within total token budget.
        Priority order: preferences > cross_session > long_term > working > short_term
        """
        if not memory_contents:
            return ""

        priority = ["preference", "cross_session", "long_term", "working", "short_term"]
        remaining = total_budget
        parts = []

        for mem_type in priority:
            if mem_type not in memory_contents:
                continue
            if remaining <= 50:  # Minimum threshold
                break

            content = memory_contents[mem_type]
            tokens = self.estimate_tokens(content)
            budget = self._budgets.get(mem_type, 200)

            # Use whichever is smaller: budget or remaining
            allowed = min(budget, remaining)

            if tokens > allowed:
                truncated = self.truncate_to_budget(content, allowed)
                parts.append(f"[{mem_type}]\n{truncated}")
                self._usage[mem_type] = allowed
            else:
                parts.append(f"[{mem_type}]\n{content}")
                self._usage[mem_type] = tokens

            remaining -= allowed

        return "\n\n".join(parts)

    def get_usage(self) -> Dict[str, int]:
        """Get token usage per memory type."""
        return self._usage.copy()

    def set_budget(self, mem_type: str, budget: int) -> None:
        """Set token budget for a memory type."""
        self._budgets[mem_type] = budget

    def reset_usage(self) -> None:
        """Reset usage counters."""
        self._usage = {k: 0 for k in self._budgets}