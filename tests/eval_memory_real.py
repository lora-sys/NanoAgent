"""Minimal real-API eval for memory cross-session persistence.

Goal: Verify memory actually persists across agent sessions with minimal API calls.

Strategy:
1. Session 1: Agent stores memory via remember tool (1 LLM call + 1 tool call)
2. Session 2: New agent instance recalls memory via recall tool (1 LLM call + 1 tool call)
3. Verify Session 2 agent correctly recalled the stored memory

Total: ~2 LLM calls for the full test.

Run:
    uv run python tests/eval_memory_real.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from core.agent import NanoAgent
from core.memory import get_memory_manager, reset_memory_manager


def test_cross_session_memory_persistence():
    """
    Core test: Store in session 1, recall in session 2 with real LLM.

    Session 1: Store key="favorite_color", value="蓝色" in long_term
    Session 2: Recall using the EXACT key from SAME store (long_term)
    """
    reset_memory_manager()
    mm = get_memory_manager()

    # Session 1: Store memory using agent with real LLM
    print("\n=== Session 1: Store memory ===")
    agent1 = NanoAgent()
    result1 = agent1.run("用remember工具记住key=favorite_color, value=蓝色, mem_type=long_term", max_iterations=5)
    print(f"Session 1 result: {result1.get('response', '')[:100]}")

    # Verify stored
    stored = mm.get_store("long_term").get("favorite_color")
    print(f"Stored value: {stored}")
    assert stored == "蓝色", f"Expected '蓝色', got '{stored}'"

    # Session 2: New agent instance recalls using EXACT key from SAME store
    print("\n=== Session 2: Recall memory ===")
    agent2 = NanoAgent()
    # Use same store (long_term) and exact key
    result2 = agent2.run("用recall工具查询query=favorite_color, mem_type=long_term", max_iterations=5)
    response2 = result2.get("response", "")
    print(f"Session 2 response: {response2[:200]}")

    # Verify recall succeeded
    assert "蓝" in response2 or "蓝色" in response2 or "blue" in response2.lower(), \
        f"Expected '蓝色' or 'blue' in response, got: {response2}"

    print("\n✅ Cross-session memory persistence verified!")


def test_preference_recall_cross_session():
    """
    Test preference memory persists across sessions.

    Session 1: Set preference "username=Alice"
    Session 2: Get preference "username" → should be "Alice"
    """
    reset_memory_manager()
    mm = get_memory_manager()

    # Session 1: Set preference
    print("\n=== Session 1: Set preference ===")
    agent1 = NanoAgent()
    result1 = agent1.run("用preference工具设置key=username, value=Alice", max_iterations=5)
    print(f"Session 1 result: {result1.get('response', '')[:100]}")

    # Verify stored
    stored = mm.get_store("preference").get_preference("username")
    print(f"Stored preference: {stored}")
    assert stored == "Alice", f"Expected 'Alice', got '{stored}'"

    # Session 2: Get preference using SAME key
    print("\n=== Session 2: Get preference ===")
    agent2 = NanoAgent()
    result2 = agent2.run("用preference工具查询key=username的值", max_iterations=5)
    response2 = result2.get("response", "")
    print(f"Session 2 response: {response2[:200]}")

    # Verify
    assert "Alice" in response2 or "alice" in response2.lower(), \
        f"Expected 'Alice' in response, got: {response2}"

    print("\n✅ Preference recall verified!")


def test_long_term_memory_recall():
    """
    Test long-term memory persists and can be recalled.

    Session 1: Store "project_language=Python" in long_term
    Session 2: Query for "project_language" from SAME store (long_term)
    """
    reset_memory_manager()
    mm = get_memory_manager()

    # Session 1: Store
    print("\n=== Session 1: Store long-term memory ===")
    agent1 = NanoAgent()
    result1 = agent1.run("用remember工具存储key=project_language, value=Python, mem_type=long_term", max_iterations=5)
    print(f"Session 1 result: {result1.get('response', '')[:100]}")

    # Verify stored
    stored = mm.get_store("long_term").get("project_language")
    print(f"Stored value: {stored}")
    assert stored == "Python", f"Expected 'Python', got '{stored}'"

    # Session 2: Recall using same store (long_term)
    print("\n=== Session 2: Recall long-term memory ===")
    agent2 = NanoAgent()
    result2 = agent2.run("用recall工具查询query=project_language, mem_type=long_term", max_iterations=5)
    response2 = result2.get("response", "")
    print(f"Session 2 response: {response2[:200]}")

    # Verify
    assert "Python" in response2 or "python" in response2.lower(), \
        f"Expected 'Python' in response, got: {response2}"

    print("\n✅ Long-term memory recall verified!")


if __name__ == "__main__":
    from llm.client import NanoLLMClient
    client = NanoLLMClient()

    if client.mock_enabled:
        print("⚠️  Mock mode enabled. Set mock.enabled=false in nanoagent.toml to run real API tests.")
        print("   Current config:", client.mock_enabled)
        import sys
        sys.exit(0)

    print("🚀 Running real API tests (mock_enabled=False)")
    print("=" * 60)

    test_cross_session_memory_persistence()
    test_preference_recall_cross_session()
    test_long_term_memory_recall()

    print("\n" + "=" * 60)
    print("All real-API memory tests passed!")
    print("=" * 60)
    print("\n" + "=" * 60)
    print("All real-API memory tests passed!")
    print("=" * 60)