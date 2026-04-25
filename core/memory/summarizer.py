"""Session summarizer — auto-summarize sessions for cross-session recall."""

from typing import Any, Dict, List, Optional
import uuid

from core.memory.stores.sqlite_store import CrossSessionStore


class SessionSummarizer:
    """
    Summarizes agent sessions and stores context for cross-session recall.
    """

    def __init__(self, store: Optional[CrossSessionStore] = None):
        self._store = store or CrossSessionStore()

    def summarize_and_save(
        self,
        task: str,
        tools_used: List[str],
        artifacts: List[str],
        response: str,
        session_id: Optional[str] = None
    ) -> str:
        """
        Summarize session and save to cross-session store.
        Returns session_id.
        """
        if session_id is None:
            session_id = str(uuid.uuid4())[:12]

        # Generate summary from session data
        summary = self._generate_summary(task, tools_used, artifacts, response)

        self._store.save_summarized_context(session_id, summary)

        # Also save full session data
        self._store.save_session(session_id, {
            "task": task,
            "tools_used": tools_used,
            "artifacts": artifacts,
            "summary": summary,
            "started_at": "",  # Will be set by store
        })

        return session_id

    def _generate_summary(
        self,
        task: str,
        tools_used: List[str],
        artifacts: List[str],
        response: str
    ) -> str:
        """Generate a summary string from session data."""
        parts = [f"Task: {task}"]
        if tools_used:
            parts.append(f"Tools: {', '.join(tools_used)}")
        if artifacts:
            parts.append(f"Artifacts: {', '.join(artifacts[:3])}")  # Limit to 3
        # Truncate response for summary
        if len(response) > 200:
            response = response[:200] + "..."
        parts.append(f"Result: {response}")
        return " | ".join(parts)

    def get_recent_sessions(self, n: int = 3) -> List[Dict[str, Any]]:
        """Get n most recent session summaries."""
        return self._store.get_recent_context(n)

    def find_related(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Find sessions related to query."""
        return self._store.find_related_context(query, limit)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get full session data."""
        return self._store.load_session(session_id)