"""Cross-session persistence tests — verify memory persists across agent instances."""

import pytest
from core.memory import (
    get_memory_manager,
    reset_memory_manager,
    AgentMemoryIntegrator,
)


class TestCrossSessionPersistence:
    """Test memory persists across sessions."""

    def test_store_and_recall_long_term(self):
        """Store in session 1, recall in session 2 (same process)."""
        reset_memory_manager()
        mm1 = get_memory_manager()

        # Session 1: store
        mm1.get_store("long_term").set("project", "nanoagent")
        mm1.get_store("long_term").set("core_modules", "agent, tools, llm")

        # Session 2: recall (fresh mm instance, same process)
        reset_memory_manager()
        mm2 = get_memory_manager()

        project = mm2.get_store("long_term").get("project")
        modules = mm2.get_store("long_term").get("core_modules")

        assert project == "nanoagent", f"Expected 'nanoagent', got '{project}'"
        assert modules == "agent, tools, llm", (
            f"Expected 'agent, tools, llm', got '{modules}'"
        )

    def test_cross_session_store_and_recall(self):
        """Test cross-session store save and recall."""
        reset_memory_manager()
        mm = get_memory_manager()
        cross = mm.get_store("cross_session")

        # Save session context
        cross.save_summarized_context("session_test", "Completed project analysis task")

        # Verify can recall
        recent = cross.get_recent_context(1)
        assert len(recent) >= 1
        assert recent[0]["session_id"] == "session_test"

    def test_preference_persists_across_sessions(self):
        """Preference set in session 1 available in session 2."""
        reset_memory_manager()
        mm1 = get_memory_manager()

        # Set preference
        mm1.get_store("preference").set_preference("theme", "dark")
        mm1.get_store("preference").set_preference("language", "中文")

        # New session
        reset_memory_manager()
        mm2 = get_memory_manager()

        theme = mm2.get_store("preference").get_preference("theme")
        language = mm2.get_store("preference").get_preference("language")

        assert theme == "dark", f"Expected 'dark', got '{theme}'"
        assert language == "中文", f"Expected '中文', got '{language}'"

    def test_hot_swap_preserves_original(self):
        """Hot-swap custom store, then restore original."""
        reset_memory_manager()
        mm = get_memory_manager()

        original = mm.get_store("long_term")
        original.set("key", "original_value")

        # Hot-swap
        from core.memory.stores import InMemoryStore

        custom = InMemoryStore()
        custom.set("key", "custom_value")

        mm.register_store("long_term", custom)
        assert mm.get_store("long_term").get("key") == "custom_value"

        # Restore
        mm.register_store("long_term", original)
        assert mm.get_store("long_term").get("key") == "original_value"

    def test_multiple_sessions_write_order(self):
        """Multiple sessions writing don't lose data."""
        reset_memory_manager()
        mm = get_memory_manager()

        sessions = [
            ("s1", "task 1 completed"),
            ("s2", "task 2 completed"),
            ("s3", "task 3 completed"),
        ]

        cross = mm.get_store("cross_session")
        for sid, summary in sessions:
            cross.save_summarized_context(sid, summary)

        # Verify all 3 are accessible
        recent = cross.get_recent_context(3)
        assert len(recent) == 3, f"Expected 3 sessions, got {len(recent)}"

        # Verify search works
        related = cross.find_related_context("task", limit=5)
        assert len(related) >= 3

    def test_agent_integrator_lifecycle(self):
        """Test AgentMemoryIntegrator hooks work."""
        reset_memory_manager()
        mm = get_memory_manager()

        integrator = AgentMemoryIntegrator(agent=None, memory_manager=mm)

        # on_agent_start should not error
        integrator.on_agent_start("test task")

        # on_tool_call should track tools
        integrator.on_tool_call("read_file")
        integrator.on_tool_call("grep")

        # on_turn_end should not error
        integrator.on_turn_end("read_file", {"status": "ok"})

        # on_agent_end should save session summary
        integrator.on_agent_end("test task", "completed task")

        # Verify session was saved
        recent = mm.get_store("cross_session").get_recent_context(1)
        assert len(recent) >= 1


class TestMemoryTools:
    """Test memory agent tools."""

    def test_remember_and_recall_via_tools(self):
        """Test remember/recall tools workflow."""
        reset_memory_manager()
        mm = get_memory_manager()

        # Simulate tool calls
        from core.memory.tools import register_memory_tools

        # Create a mock registry
        class MockRegistry:
            def __init__(self):
                self._tools = {}

            def register(self, name, func, desc):
                self._tools[name] = func

            def execute(self, name, args):
                return self._tools[name](**args)

        registry = MockRegistry()
        register_memory_tools(registry)

        # Test remember
        result = registry.execute(
            "remember",
            {"key": "test_key", "value": "test_value", "mem_type": "long_term"},
        )
        assert result["status"] == "ok"

        # Test recall
        result = registry.execute(
            "recall", {"query": "test_key", "mem_type": "long_term"}
        )
        assert result["status"] == "ok"
        # Value should be retrievable
        stored = mm.get_store("long_term").get("test_key")
        assert stored == "test_value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
