"""Memory manager — central orchestrator with hot-swappable stores."""

from typing import Dict, Optional

from core.memory.interfaces import BaseMemory
from core.memory.stores import (
    InMemoryStore,
    WorkingMemoryStore,
    SQLiteMemoryStore,
    CrossSessionStore,
    FileBackedMemoryStore,
)
from core.memory.optimizer import MemoryOptimizer


class MemoryManager:
    """
    Central memory orchestrator with hot-swappable stores.

    Usage:
        mm = get_memory_manager()
        mm.set_store("long_term", CustomMemoryStore())  # hot-swap
        mm.get_store("long_term").search_sessions("python", limit=5)
    """

    def __init__(self):
        self._stores: Dict[str, BaseMemory] = {}
        self._optimizer = MemoryOptimizer()
        self._register_default_stores()

    def _register_default_stores(self) -> None:
        """Register default in-memory stores."""
        self._stores["short_term"] = InMemoryStore()
        self._stores["working"] = WorkingMemoryStore()
        self._stores["long_term"] = SQLiteMemoryStore()
        self._stores["cross_session"] = CrossSessionStore()
        self._stores["preference"] = FileBackedMemoryStore()

    def register_store(self, name: str, store: BaseMemory) -> None:
        """Hot-swap a memory store at runtime."""
        self._stores[name] = store

    def get_store(self, name: str) -> Optional[BaseMemory]:
        """Get store by name."""
        return self._stores.get(name)

    def set_store(self, name: str, store: BaseMemory) -> None:
        """Set or replace a store (alias for register_store)."""
        self._stores[name] = store

    def build_context_for_prompt(self, max_tokens: int = 2000) -> str:
        """
        Build memory context string within token budget.
        Priority: preference > cross_session > long_term > working > short_term
        """
        contents = {}
        for name in ["preference", "cross_session", "long_term", "working", "short_term"]:
            store = self._stores.get(name)
            if store:
                ctx = store.to_context_string(max_tokens=self._optimizer._budgets.get(name, 200))
                if ctx:
                    contents[name] = ctx

        return self._optimizer.build_context(contents, total_budget=max_tokens)

    def clear_all(self) -> None:
        """Clear all memory stores."""
        for store in self._stores.values():
            store.clear()

    @property
    def optimizer(self) -> MemoryOptimizer:
        return self._optimizer

    def reset(self) -> None:
        """Reset all stores and optimizer."""
        self._stores.clear()
        self._register_default_stores()
        self._optimizer.reset_usage()


# Global singleton
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get or create global MemoryManager singleton."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


def reset_memory_manager() -> None:
    """Reset global MemoryManager (for testing)."""
    global _memory_manager
    if _memory_manager is not None:
        _memory_manager.reset()
        _memory_manager = None