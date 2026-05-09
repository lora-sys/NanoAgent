"""NanoAgent Memory System — hot-swappable memory framework.

Usage:
    from core.memory import get_memory_manager, register_store

    mm = get_memory_manager()
    mm.get_store("long_term").set("my_key", "my_value")
    mm.get_store("long_term").get("my_key")  # "my_value"

    # Hot-swap with custom store
    mm.register_store("long_term", MyCustomStore())
"""

from core.memory.interfaces import (
    BaseMemory,
    SessionMemory,
    WorkingMemory,
    LongTermMemory,
    PreferenceMemory,
    CrossSessionMemory,
    MemoryConfig,
    MemoryStats,
)
from core.memory.manager import (
    MemoryManager,
    get_memory_manager,
    reset_memory_manager,
)
from core.memory.optimizer import MemoryOptimizer
from core.memory.summarizer import SessionSummarizer
from core.memory.stores import (
    InMemoryStore,
    WorkingMemoryStore,
    SQLiteMemoryStore,
    CrossSessionStore,
    FileBackedMemoryStore,
)
from core.memory.tools import register_memory_tools
from core.memory.integrators import AgentMemoryIntegrator

__all__ = [
    # Interfaces
    "BaseMemory",
    "SessionMemory",
    "WorkingMemory",
    "LongTermMemory",
    "PreferenceMemory",
    "CrossSessionMemory",
    "MemoryConfig",
    "MemoryStats",
    # Manager
    "MemoryManager",
    "get_memory_manager",
    "reset_memory_manager",
    # Optimizer
    "MemoryOptimizer",
    # Summarizer
    "SessionSummarizer",
    # Stores
    "InMemoryStore",
    "WorkingMemoryStore",
    "SQLiteMemoryStore",
    "CrossSessionStore",
    "FileBackedMemoryStore",
    # Tools
    "register_memory_tools",
    # Integrators
    "AgentMemoryIntegrator",
]
