"""Agent memory integrator — hooks memory into NanoAgent lifecycle."""

from typing import Optional

from core.memory.manager import get_memory_manager, MemoryManager
from core.memory.summarizer import SessionSummarizer


class AgentMemoryIntegrator:
    """
    Hooks memory into NanoAgent lifecycle via lifecycle events.

    On AgentStartEvent: Inject memory context into system prompt
    On AgentEndEvent: Save session summary to cross-session memory
    On TurnEndEvent: Store tool results in working memory
    """

    def __init__(
        self,
        agent,
        memory_manager: Optional[MemoryManager] = None,
        summarizer: Optional[SessionSummarizer] = None,
    ):
        self.agent = agent
        self.mm = memory_manager or get_memory_manager()
        self.summarizer = summarizer or SessionSummarizer()
        self._current_session_id: Optional[str] = None
        self._session_tools: list[str] = []
        self._session_artifacts: list[str] = []

    def on_agent_start(self, task: str) -> None:
        """Initialize session memory and inject context."""
        import uuid

        self._current_session_id = str(uuid.uuid4())[:12]
        self._session_tools = []
        self._session_artifacts = []

        # Inject memory context into system prompt if agent is available
        mem_context = self.mm.build_context_for_prompt(max_tokens=1500)
        if (
            mem_context
            and self.agent
            and hasattr(self.agent, "conversation")
            and self.agent.conversation
        ):
            # Prepend memory context to system message
            system_msg = self.agent.conversation[0]
            if system_msg.get("role") == "system":
                original = system_msg.get("content", "")
                system_msg["content"] = (
                    f"{original}\n\n## Memory Context\n{mem_context}\n"
                )

    def on_tool_call(self, tool_name: str) -> None:
        """Track tool usage for session summary."""
        if tool_name not in self._session_tools:
            self._session_tools.append(tool_name)

    def on_artifact(self, artifact: str) -> None:
        """Track artifacts for session summary."""
        if artifact and artifact not in self._session_artifacts:
            self._session_artifacts.append(artifact)

    def on_agent_end(self, task: str, response: str) -> None:
        """Save session summary to cross-session memory."""
        if self._current_session_id is None:
            return

        self.summarizer.summarize_and_save(
            task=task,
            tools_used=self._session_tools,
            artifacts=self._session_artifacts,
            response=response,
            session_id=self._current_session_id,
        )

        # Also save key info to long-term memory if important
        # (this could be enhanced with importance scoring)

    def on_turn_end(self, tool_name: str, result: dict) -> None:
        """Store tool results in working memory."""
        working = self.mm.get_store("working")
        if working and hasattr(working, "add_tool_result"):
            working.add_tool_result(tool_name, result)
