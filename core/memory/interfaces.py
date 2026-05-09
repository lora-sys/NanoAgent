"""Memory interfaces — ABCs for all memory types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar


K = TypeVar("K")
V = TypeVar("V")


@dataclass
class MemoryConfig:
    """Configuration for memory stores."""

    max_tokens: int = 2000
    ttl_seconds: Optional[int] = None  # None = forever


@dataclass
class MemoryStats:
    """Statistics for memory store."""

    hits: int = 0
    misses: int = 0
    total_tokens: int = 0
    last_updated: Optional[datetime] = None


class BaseMemory(ABC):
    """Abstract base for all memory types."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve value by key."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Store value by key."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove value by key."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all memory."""
        pass

    @abstractmethod
    def to_context_string(self, max_tokens: int = 1000) -> str:
        """Serialize to context string for LLM prompt. Must respect token budget."""
        pass

    @property
    @abstractmethod
    def memory_type(self) -> str:
        """Return memory type identifier."""
        pass

    @property
    def stats(self) -> MemoryStats:
        """Return memory statistics."""
        return MemoryStats()


class SessionMemory(BaseMemory):
    """Ephemeral memory for a single conversation turn."""

    @property
    def memory_type(self) -> str:
        return "short_term"


class WorkingMemory(BaseMemory):
    """Memory active during agent execution session."""

    @abstractmethod
    def add_tool_result(self, tool_name: str, result: Any) -> None:
        """Record tool execution result for potential recall."""
        pass

    @abstractmethod
    def get_recent_results(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get n most recent tool results."""
        pass

    @property
    def memory_type(self) -> str:
        return "working"


class LongTermMemory(BaseMemory):
    """Persistent storage across sessions."""

    @abstractmethod
    def save_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Save completed session data."""
        pass

    @abstractmethod
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data by ID."""
        pass

    @abstractmethod
    def search_sessions(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search across session summaries."""
        pass

    @property
    def memory_type(self) -> str:
        return "long_term"


class PreferenceMemory(BaseMemory):
    """User settings, habits, configurations."""

    @abstractmethod
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference."""
        pass

    @abstractmethod
    def set_preference(self, key: str, value: Any) -> None:
        """Set user preference."""
        pass

    @abstractmethod
    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all preferences as dict."""
        pass

    @property
    def memory_type(self) -> str:
        return "preference"


class CrossSessionMemory(BaseMemory):
    """Remembers context between sessions."""

    @abstractmethod
    def save_summarized_context(self, session_id: str, summary: str) -> None:
        """Save session summary for cross-session recall."""
        pass

    @abstractmethod
    def get_recent_context(self, n: int = 3) -> List[Dict[str, Any]]:
        """Get n most recent session summaries."""
        pass

    @abstractmethod
    def find_related_context(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Find context related to query."""
        pass

    @property
    def memory_type(self) -> str:
        return "cross_session"
