"""Memory system tests."""

import pytest
from core.memory import (
    get_memory_manager,
    InMemoryStore,
    WorkingMemoryStore,
    SQLiteMemoryStore,
    CrossSessionStore,
    FileBackedMemoryStore,
    MemoryOptimizer,
)


class TestInMemoryStore:
    """Tests for InMemoryStore."""

    def test_basic_set_get(self):
        store = InMemoryStore()
        store.set("key1", "value1")
        assert store.get("key1") == "value1"

    def test_get_default(self):
        store = InMemoryStore()
        assert store.get("nonexistent", "default") == "default"

    def test_delete(self):
        store = InMemoryStore()
        store.set("key1", "value1")
        store.delete("key1")
        assert store.get("key1") is None

    def test_clear(self):
        store = InMemoryStore()
        store.set("key1", "value1")
        store.set("key2", "value2")
        store.clear()
        assert store.get("key1") is None
        assert store.get("key2") is None

    def test_to_context_string(self):
        store = InMemoryStore()
        store.set("name", "Alice")
        store.set("theme", "dark")
        ctx = store.to_context_string(max_tokens=200)
        assert "name" in ctx
        assert "Alice" in ctx


class TestWorkingMemoryStore:
    """Tests for WorkingMemoryStore."""

    def test_add_tool_result(self):
        store = WorkingMemoryStore()
        store.add_tool_result("read_file", {"path": "test.py"})
        results = store.get_recent_results(5)
        assert len(results) == 1
        assert results[0]["tool"] == "read_file"

    def test_tool_result_limit(self):
        store = WorkingMemoryStore()
        for i in range(15):
            store.add_tool_result(f"tool_{i}", {"idx": i})
        results = store.get_recent_results(10)
        assert len(results) <= 10


class TestSQLiteMemoryStore:
    """Tests for SQLiteMemoryStore."""

    def test_persistent_set_get(self):
        store = SQLiteMemoryStore()
        store.set("test_key", "test_value")
        assert store.get("test_key") == "test_value"

    def test_delete(self):
        store = SQLiteMemoryStore()
        store.set("del_key", "del_value")
        store.delete("del_key")
        assert store.get("del_key") is None

    def test_clear(self):
        store = SQLiteMemoryStore()
        store.set("key1", "value1")
        store.set("key2", "value2")
        store.clear()
        assert store.get("key1") is None


class TestFileBackedMemoryStore:
    """Tests for FileBackedMemoryStore."""

    def test_set_get_preference(self):
        store = FileBackedMemoryStore()
        store.set_preference("name", "Bob")
        assert store.get_preference("name") == "Bob"

    def test_get_all_preferences(self):
        store = FileBackedMemoryStore()
        store.set_preference("key1", "val1")
        store.set_preference("key2", "val2")
        prefs = store.get_all_preferences()
        assert "key1" in prefs
        assert prefs["key1"] == "val1"


class TestMemoryOptimizer:
    """Tests for MemoryOptimizer."""

    def test_estimate_tokens(self):
        opt = MemoryOptimizer()
        assert opt.estimate_tokens("1234") == 1  # 4 chars = 1 token
        assert opt.estimate_tokens("a" * 100) == 25

    def test_truncate_to_budget(self):
        opt = MemoryOptimizer()
        text = "a" * 1000
        truncated = opt.truncate_to_budget(text, 10)
        # 10 tokens * 4 chars = 40 chars + "..." (3 chars) = 43 total
        assert len(truncated) <= 45  # 40 + some margin for "..."

    def test_build_context(self):
        opt = MemoryOptimizer()
        contents = {
            "preference": "user: Alice",
            "long_term": "project: nanoagent",
        }
        ctx = opt.build_context(contents, total_budget=500)
        assert "preference" in ctx or "Alice" in ctx


class TestMemoryManager:
    """Tests for MemoryManager."""

    def test_singleton(self):
        mm1 = get_memory_manager()
        mm2 = get_memory_manager()
        assert mm1 is mm2

    def test_get_store(self):
        mm = get_memory_manager()
        assert mm.get_store("short_term") is not None
        assert mm.get_store("long_term") is not None
        assert mm.get_store("preference") is not None

    def test_register_store(self):
        mm = get_memory_manager()
        original = mm.get_store("long_term")
        custom = InMemoryStore()
        mm.register_store("long_term", custom)
        assert mm.get_store("long_term") is custom
        mm.register_store("long_term", original)  # restore

    def test_build_context(self):
        mm = get_memory_manager()
        ctx = mm.build_context_for_prompt(max_tokens=1000)
        assert isinstance(ctx, str)


class TestCrossSessionStore:
    """Tests for CrossSessionStore."""

    def test_save_and_recall_context(self):
        store = CrossSessionStore()
        store.save_summarized_context("test_session", "Test summary content")
        recent = store.get_recent_context(1)
        assert len(recent) >= 1

    def test_find_related_context(self):
        store = CrossSessionStore()
        store.save_summarized_context("s1", "Project analysis task")
        related = store.find_related_context("analysis", limit=5)
        assert isinstance(related, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
