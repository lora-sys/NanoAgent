"""Complex memory eval scenarios — 测试复杂提示词环境下记忆系统表现.

Goal: 验证记忆系统在复杂场景下能否准确完成任务
- 多步记忆操作
- 相似key区分
- 复杂查询推理
- 热插拔场景
- 上下文注入效果

Run: uv run python tests/eval_memory_complex.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import NanoAgent
from core.memory import get_memory_manager, reset_memory_manager, InMemoryStore


def test_multi_step_memory():
    """多步记忆操作 — 验证能按顺序完成多个记忆任务。"""
    print("\n" + "=" * 60)
    print("Test 1: Multi-step memory operations")
    print("=" * 60)

    reset_memory_manager()
    mm = get_memory_manager()

    # Store explicitly with exact keys
    stores = [
        ("employee_id", "A12345"),
        ("department", "研发部"),
        ("title", "工程师"),
    ]

    # Session 1: Store all with explicit key names
    agent1 = NanoAgent()
    for key, value in stores:
        print(f"\n→ Storing: {key}={value}")
        result = agent1.run(
            f"用remember工具记住key={key}, value={value}, mem_type=long_term",
            max_iterations=3,
        )
        stored = mm.get_store("long_term").get(key)
        print(f"  Stored: {stored}")
        # Agent may store with slight variations - check value exists
        assert stored == value, f"Expected {value}, got {stored}"

    # Session 2: Verify all can be recalled
    print("\n--- Session 2: Verify all stored ---")
    agent2 = NanoAgent()
    for key, expected in stores:
        print(f"\n→ Recalling: {key}")
        result = agent2.run(
            f"用recall工具查询query={key}, mem_type=long_term", max_iterations=3
        )
        response = result.get("response", "")
        print(f"  Response: {response[:100]}")
        # Each should recall its specific value
        assert expected in response, f"Failed to recall {key}"

    print("✅ Multi-step memory test passed!")


def test_similar_keys():
    """相似key区分 — 测试系统能否区分相似的记忆key。"""
    print("\n" + "=" * 60)
    print("Test 2: Similar keys discrimination")
    print("=" * 60)

    reset_memory_manager()
    mm = get_memory_manager()

    # Store similar keys with different values
    similar_keys = [
        ("user_name", "Alice"),
        ("user_email", "alice@example.com"),
        ("user_password", "secret123"),
    ]

    agent1 = NanoAgent()
    for key, value in similar_keys:
        result = agent1.run(
            f"用remember工具记住key={key}, value={value}, mem_type=long_term",
            max_iterations=3,
        )
        stored = mm.get_store("long_term").get(key)
        assert stored == value, f"Expected {value}, got {stored}"

    # Recall each and verify exact match
    agent2 = NanoAgent()
    for key, expected in similar_keys:
        result = agent2.run(
            f"用recall工具查询key={key}, mem_type=long_term", max_iterations=3
        )
        response = result.get("response", "")
        print(f"  {key} → {response[:60]}...")
        assert expected in response, f"Failed to recall exact {key}"

    print("✅ Similar keys discrimination test passed!")


def test_context_injection():
    """上下文注入 — 测试记忆上下文是否正确注入到agent系统提示。"""
    print("\n" + "=" * 60)
    print("Test 3: Memory context injection")
    print("=" * 60)

    reset_memory_manager()
    mm = get_memory_manager()

    # Pre-populate memory
    mm.get_store("preference").set_preference("language", "中文")
    mm.get_store("long_term").set("project", "nanoagent")
    mm.get_store("cross_session").save_summarized_context("s1", "completed task A")

    # Build context
    ctx = mm.build_context_for_prompt(max_tokens=500)
    print(f"Built context ({len(ctx)} chars):\n{ctx[:200]}...")

    # Verify context contains our stored data
    assert "nanoagent" in ctx.lower(), "project not in context"
    assert "中文" in ctx or "language" in ctx.lower(), "language not in context"

    # Agent should have access to this context via memory_integrator
    from core.memory.integrators import AgentMemoryIntegrator

    class MockAgent:
        conversation = [{"role": "system", "content": "base system prompt"}]

    integrator = AgentMemoryIntegrator(agent=MockAgent(), memory_manager=mm)
    integrator.on_agent_start("test task")

    # Context should be injected
    modified_content = MockAgent.conversation[0]["content"]
    print(
        f"\nModified system prompt contains memory: {'Memory Context' in modified_content}"
    )
    assert "Memory Context" in modified_content or "nanoagent" in modified_content

    print("✅ Memory context injection test passed!")


def test_hot_swap_under_operations():
    """热插拔下操作 — 测试热插拔后记忆是否正常工作。"""
    print("\n" + "=" * 60)
    print("Test 4: Hot-swap under operations")
    print("=" * 60)

    reset_memory_manager()
    mm = get_memory_manager()

    # Store in SQLite first
    original = mm.get_store("long_term")
    mm.get_store("long_term").set("sqlite_key", "from_sqlite")

    # Hot-swap to InMemory
    in_mem = InMemoryStore()
    mm.register_store("long_term", in_mem)
    mm.get_store("long_term").set("memory_key", "from_memory")

    # Verify InMemory works
    assert mm.get_store("long_term").get("memory_key") == "from_memory"

    # Restore SQLite
    mm.register_store("long_term", original)

    # Verify SQLite restored, InMemory data gone
    assert mm.get_store("long_term").get("sqlite_key") == "from_sqlite"
    assert mm.get_store("long_term").get("memory_key") is None

    print("✅ Hot-swap under operations test passed!")


def test_complex_query():
    """复杂查询推理 — 测试能否基于记忆进行复杂查询。"""
    print("\n" + "=" * 60)
    print("Test 5: Complex query reasoning")
    print("=" * 60)

    reset_memory_manager()
    mm = get_memory_manager()

    # Store structured information with explicit keys
    agent1 = NanoAgent()
    memories = [
        ("location", "北京市朝阳区"),
        ("job", "软件工程师"),
        ("languages", "Python, Go"),
    ]

    for key, value in memories:
        result = agent1.run(
            f"用remember工具记住key={key}, value={value}, mem_type=long_term",
            max_iterations=3,
        )
        stored = mm.get_store("long_term").get(key)
        print(f"  Stored {key}: {stored}")

    # Query that requires reasoning across multiple memories
    # Key insight: query the KEY, not natural language, for best results
    agent2 = NanoAgent()
    result = agent2.run(
        "查询languages这个key在long_term里的值是什么？用recall工具", max_iterations=5
    )
    response = result.get("response", "")
    print(f"\nComplex query response:\n{response[:200]}")

    # Should find Python in the languages field
    assert "Python" in response or "python" in response.lower(), (
        "Expected 'Python' in complex query response"
    )

    print("✅ Complex query reasoning test passed!")


def test_cross_session_search():
    """跨会话搜索 — 测试能否从历史会话中搜索相关信息。"""
    print("\n" + "=" * 60)
    print("Test 6: Cross-session search")
    print("=" * 60)

    reset_memory_manager()
    mm = get_memory_manager()
    cross = mm.get_store("cross_session")

    # Simulate multiple past sessions
    sessions = [
        ("session_1", "完成了项目A的开发，使用React前端"),
        ("session_2", "修复了项目B的bug，涉及Python后端"),
        ("session_3", "完成了项目C的设计，使用Go语言"),
    ]

    for sid, summary in sessions:
        cross.save_summarized_context(sid, summary)
        print(f"  Saved: {sid} → {summary[:40]}...")

    # Search for Python-related work
    agent = NanoAgent()
    result = agent.run(
        "搜索我之前关于Python的会话经验，用recall工具查询", max_iterations=3
    )
    response = result.get("response", "")
    print(f"\nSearch response:\n{response[:200]}")

    # Should find session_2 about Python bug fix
    assert "Python" in response or "python" in response.lower() or "bug" in response, (
        "Expected Python-related content in cross-session search"
    )

    print("✅ Cross-session search test passed!")


def run_all_tests():
    """运行所有复杂场景测试。"""
    print("\n" + "=" * 60)
    print("NanoAgent Memory Complex Scenarios Eval")
    print("=" * 60)

    from llm.client import NanoLLMClient

    client = NanoLLMClient()

    if client.mock_enabled:
        print("⚠️  Mock mode enabled. Skipping real API tests.")
        print("   Set mock.enabled=false in nanoagent.toml to run.")
        return

    tests = [
        test_multi_step_memory,
        test_similar_keys,
        test_context_injection,
        test_hot_swap_under_operations,
        test_complex_query,
        test_cross_session_search,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
