"""Memory optimizer — token budget management."""

import re
from typing import Dict, List, Optional, Tuple


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

    # Task-type based budgets (key = dominant keyword)
    TASK_BUDGETS: Dict[str, Dict[str, int]] = {
        "tool_heavy": {  # read_file, grep, edit_file focused
            "preference": 150,
            "cross_session": 200,
            "long_term": 200,
            "working": 350,
            "short_term": 150,
        },
        "analysis": {  # analyze, design, architect focused
            "preference": 100,
            "cross_session": 500,
            "long_term": 500,
            "working": 150,
            "short_term": 50,
        },
        "creative": {  # write, create, generate focused
            "preference": 200,
            "cross_session": 300,
            "long_term": 400,
            "working": 200,
            "short_term": 200,
        },
    }

    def __init__(self, budgets: Dict[str, int] | None = None):
        self._budgets = budgets or self.DEFAULT_BUDGETS.copy()
        self._usage: Dict[str, int] = {k: 0 for k in self._budgets}
        self._task_type: Optional[str] = None

    def estimate_tokens(self, text: str) -> int:
        """
        Token estimation with language-aware adjustment.

        For Chinese: ~1.5-2 chars per token
        For English: ~3.5-4 chars per token
        Mixed content: weighted average
        """
        if not text:
            return 0

        # Count Chinese characters (CJK range)
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', text))

        # Count other characters
        other_chars = len(text) - chinese_chars

        # Estimate: Chinese ~1.8 chars/token, English ~4 chars/token
        chinese_tokens = chinese_chars / 1.8
        english_tokens = other_chars / 4.0

        return int(chinese_tokens + english_tokens)

    def truncate_to_budget(self, text: str, max_tokens: int) -> str:
        """
        Sentence-aware truncation that preserves complete sentences.

        Splits on sentence boundaries (Chinese: 。！？, English: .!?)
        and ensures we don't cut mid-sentence.
        """
        if not text:
            return ""

        # Estimate char budget (rough: 4 chars per token for mixed, 2 for Chinese-heavy)
        budget_chars = max_tokens * 3  # More conservative ratio

        if len(text) <= budget_chars:
            return text

        # Split into sentences (preserve delimiter)
        sentence_pattern = re.compile(r'(?<=[。！？.!?])\s*')
        sentences = sentence_pattern.split(text)

        result = ""
        remaining_chars = budget_chars - 3  # Leave room for "..."

        for sentence in sentences:
            if len(result) + len(sentence) + 1 <= remaining_chars:
                result += sentence + " "
            else:
                # If first sentence already too long, head-truncate it
                if not result:
                    return text[:budget_chars - 3] + "..."
                break

        return result.strip() + "..."

    def apply_task_budget(self, task: str) -> None:
        """
        Apply task-specific token budgets based on task content.

        Args:
            task: Task description to analyze
        """
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["读取", "搜索", "grep", "read", "list", "文件"]):
            self._task_type = "tool_heavy"
            self._budgets = self.TASK_BUDGETS["tool_heavy"].copy()
        elif any(kw in task_lower for kw in ["分析", "设计", "评估", "analyze", "design", "architect"]):
            self._task_type = "analysis"
            self._budgets = self.TASK_BUDGETS["analysis"].copy()
        elif any(kw in task_lower for kw in ["写", "创建", "生成", "write", "create", "generate"]):
            self._task_type = "creative"
            self._budgets = self.TASK_BUDGETS["creative"].copy()
        else:
            self._task_type = None
            self._budgets = self.DEFAULT_BUDGETS.copy()

    def build_context(
        self,
        memory_contents: Dict[str, str],
        total_budget: int = 2000
    ) -> str:
        """
        Build context string from multiple memory sources within total token budget.
        Priority order: preference > cross_session > long_term > working > short_term

        Respects per-type budgets and truncates with sentence awareness.
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

    def get_stats(self) -> Dict[str, any]:
        """Get optimizer statistics for debugging."""
        return {
            "task_type": self._task_type,
            "budgets": self._budgets.copy(),
            "usage": self._usage.copy(),
        }