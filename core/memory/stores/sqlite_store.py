"""SQLite-backed store — persistent long-term and cross-session memory."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.memory.interfaces import BaseMemory, LongTermMemory, CrossSessionMemory, MemoryStats


def _get_db_path() -> Path:
    """Get memory database path."""
    db_path = Path.home() / ".nanoagent"
    db_path.mkdir(parents=True, exist_ok=True)
    return db_path / "memory.db"


def _init_db() -> None:
    """Initialize memory database schema."""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            task TEXT,
            started_at TEXT,
            ended_at TEXT,
            summary TEXT,
            tools_used TEXT,
            artifacts TEXT,
            metadata TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_entries (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            key TEXT,
            value TEXT,
            created_at TEXT,
            access_count INTEGER DEFAULT 1,
            last_accessed TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_memory_session
        ON memory_entries(session_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_memory_key
        ON memory_entries(key)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_sessions_summary
        ON sessions(summary)
    """)

    conn.commit()
    conn.close()


class SQLiteMemoryStore(BaseMemory):
    """
    Persistent memory backed by SQLite at ~/.nanoagent/memory.db.
    Used for long-term memory entries.
    """

    def __init__(self):
        _init_db()
        self._db_path = _get_db_path()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def get(self, key: str, default: Any = None) -> Any:
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT value FROM memory_entries WHERE key = ? ORDER BY last_accessed DESC LIMIT 1",
            (key,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            # Update access count
            conn2 = self._conn()
            cursor2 = conn2.cursor()
            cursor2.execute(
                "UPDATE memory_entries SET access_count = access_count + 1, last_accessed = ? WHERE key = ?",
                (datetime.now().isoformat(), key)
            )
            conn2.commit()
            conn2.close()
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return row[0]
        return default

    def set(self, key: str, value: Any) -> None:
        conn = self._conn()
        cursor = conn.cursor()
        import uuid
        entry_id = str(uuid.uuid4())[:12]

        # Serialize value
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value)
        else:
            value_str = str(value)

        now = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT OR REPLACE INTO memory_entries (id, key, value, created_at, last_accessed, access_count)
            VALUES (
                COALESCE((SELECT id FROM memory_entries WHERE key = ?), ?),
                ?, ?, ?, ?, 1
            )
            """,
            (key, entry_id, key, value_str, now, now)
        )
        conn.commit()
        conn.close()

    def delete(self, key: str) -> None:
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memory_entries WHERE key = ?", (key,))
        conn.commit()
        conn.close()

    def clear(self) -> None:
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memory_entries")
        conn.commit()
        conn.close()

    def to_context_string(self, max_tokens: int = 1000) -> str:
        budget_chars = max_tokens * 4
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT key, value FROM memory_entries ORDER BY access_count DESC LIMIT 20"
        )
        rows = cursor.fetchall()
        conn.close()

        parts = []
        current_len = 0
        for key, value in rows:
            try:
                v = json.loads(value)
            except json.JSONDecodeError:
                v = value
            entry = f"{key}: {v}"
            if current_len + len(entry) + 2 <= budget_chars:
                parts.append(entry)
                current_len += len(entry) + 2
            else:
                break

        return "\n".join(parts)

    @property
    def memory_type(self) -> str:
        return "long_term"

    @property
    def stats(self) -> MemoryStats:
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(access_count) FROM memory_entries")
        row = cursor.fetchone()
        conn.close()
        return MemoryStats(total_tokens=row[0] or 0)


class CrossSessionStore(SQLiteMemoryStore):
    """
    Cross-session memory — stores session summaries for recall.
    """

    def __init__(self):
        super().__init__()
        self._db_path = _get_db_path()

    def save_summarized_context(self, session_id: str, summary: str) -> None:
        """Save session summary."""
        conn = self._conn()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT OR REPLACE INTO sessions (id, summary, ended_at)
            VALUES (?, ?, ?)
            """,
            (session_id, summary, now)
        )
        conn.commit()
        conn.close()

    def get_recent_context(self, n: int = 3) -> List[Dict[str, Any]]:
        """Get n most recent session summaries."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, task, summary, ended_at FROM sessions ORDER BY ended_at DESC LIMIT ?",
            (n,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            {"session_id": r[0], "task": r[1], "summary": r[2], "ended_at": r[3]}
            for r in rows
        ]

    def find_related_context(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Find context related to query via LIKE search."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, task, summary, ended_at FROM sessions
            WHERE summary LIKE ? OR task LIKE ?
            ORDER BY ended_at DESC LIMIT ?
            """,
            (f"%{query}%", f"%{query}%", limit)
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            {"session_id": r[0], "task": r[1], "summary": r[2], "ended_at": r[3]}
            for r in rows
        ]

    def save_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Save full session data (implements LongTermMemory)."""
        conn = self._conn()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT OR REPLACE INTO sessions
            (id, task, started_at, ended_at, summary, tools_used, artifacts, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                data.get("task", ""),
                data.get("started_at", now),
                now,
                data.get("summary", ""),
                json.dumps(data.get("tools_used", [])),
                json.dumps(data.get("artifacts", [])),
                json.dumps(data.get("metadata", {}))
            )
        )
        conn.commit()
        conn.close()

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session by ID."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, task, started_at, ended_at, summary, tools_used, artifacts, metadata FROM sessions WHERE id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row[0],
                "task": row[1],
                "started_at": row[2],
                "ended_at": row[3],
                "summary": row[4],
                "tools_used": json.loads(row[5]) if row[5] else [],
                "artifacts": json.loads(row[6]) if row[6] else [],
                "metadata": json.loads(row[7]) if row[7] else {}
            }
        return None

    def search_sessions(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search sessions by query (implements LongTermMemory)."""
        return self.find_related_context(query, limit)

    @property
    def memory_type(self) -> str:
        return "cross_session"

    def to_context_string(self, max_tokens: int = 1000) -> str:
        """
        Convert cross-session context to natural language format.

        Format: "Session: task summary | Tools: tool1, tool2 | Result: outcome"
        """
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, task, summary, tools_used FROM sessions ORDER BY ended_at DESC LIMIT 5"
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return ""

        # Build natural language context
        parts = []
        for i, (sid, task, summary, tools_used) in enumerate(rows, 1):
            # Parse tools_used JSON
            tool_list = ""
            if tools_used:
                try:
                    tools = json.loads(tools_used)
                    if tools:
                        tool_list = f" | Tools: {', '.join(tools[:5])}"  # Limit to 5 tools
                except json.JSONDecodeError:
                    pass

            # Build sentence: "Session 1: completed analysis task | Tools: read_file, grep"
            task_short = (task or summary or "unknown task")[:50]
            entry = f"Session {i}: {task_short}{tool_list}"
            parts.append(entry)

        return "\n".join(parts)