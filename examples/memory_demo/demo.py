"""Memory Demo — 展示记忆系统的各种功能.

运行方式:
    uv run python examples/memory_demo/demo.py
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
from core.memory import (
    get_memory_manager,
    reset_memory_manager,
    MemoryManager,
    MemoryOptimizer,
    InMemoryStore,
    WorkingMemoryStore,
    SQLiteMemoryStore,
    CrossSessionStore,
    FileBackedMemoryStore,
)


def demo_basic_operations():
    """基础记忆操作演示。"""
    print("\n" + "=" * 60)
    print("基础记忆操作")
    print("=" * 60)

    mm = get_memory_manager()

    # Preference store
    pref = mm.get_store("preference")
    pref.set_preference("name", "Alice")
    pref.set_preference("theme", "dark")
    print(f"\n📝 Preference: name={pref.get_preference('name')}")

    all_prefs = pref.get_all_preferences()
    print(f"📋 All preferences: {all_prefs}")

    # Long-term store
    lt = mm.get_store("long_term")
    lt.set("project_name", "nanoagent")
    lt.set("core_modules", "agent, tools, llm")
    print(f"\n💾 Long-term: project_name={lt.get('project_name')}")

    # Working store
    working = mm.get_store("working")
    working.set("current_task", "implementing memory")
    working.add_tool_result("read_file", {"path": "test.py", "lines": 100})
    print(f"\n⚡ Working memory: current_task={working.get('current_task')}")
    recent = working.get_recent_results(3)
    print(f"⚡ Recent tool results: {len(recent)} items")

    # Context string
    ctx = mm.build_context_for_prompt(max_tokens=500)
    print(f"\n📤 Context string ({len(ctx)} chars):\n{ctx[:200]}...")


def demo_hot_swap():
    """热插拔演示。"""
    print("\n" + "=" * 60)
    print("热插拔存储")
    print("=" * 60)

    mm = get_memory_manager()

    # 原始 store
    original_lt = mm.get_store("long_term")
    print(f"\n原始 long_term store: {type(original_lt).__name__}")

    # 热插拔为 InMemoryStore
    custom_store = InMemoryStore()
    custom_store.set("custom_key", "custom_value")

    mm.register_store("long_term", custom_store)
    print(f"热插拔后 long_term store: {type(mm.get_store('long_term')).__name__}")

    # 验证自定义 store 生效
    val = mm.get_store("long_term").get("custom_key")
    print(f"自定义 store 读取: {val}")

    # 恢复原始 store
    mm.register_store("long_term", original_lt)
    print("已恢复原始 store")


def demo_cross_session():
    """跨会话记忆演示。"""
    print("\n" + "=" * 60)
    print("跨会话记忆")
    print("=" * 60)

    mm = get_memory_manager()
    cross = mm.get_store("cross_session")

    # 保存多个会话摘要
    cross.save_summarized_context("session_1", "完成了项目架构设计 | Tools: read_file, grep")
    cross.save_summarized_context("session_2", "实现了记忆系统模块 | Tools: edit_file, run_bash")
    cross.save_summarized_context("session_3", "优化了 token 使用 | Tools: grep")

    # 获取最近的会话
    recent = cross.get_recent_context(3)
    print(f"\n最近 3 个会话:")
    for ctx in recent:
        print(f"  - {ctx.get('session_id', 'unknown')}: {ctx.get('summary', '')[:50]}...")

    # 搜索相关会话
    related = cross.find_related_context("记忆", limit=3)
    print(f"\n搜索 '记忆' 相关会话: {len(related)} 个结果")


def demo_token_optimization():
    """Token 优化演示。"""
    print("\n" + "=" * 60)
    print("Token 优化")
    print("=" * 60)

    mm = get_memory_manager()
    optimizer = mm.optimizer

    # 设置一些数据
    mm.get_store("preference").set_preference("user", "Alice")
    mm.get_store("long_term").set("project", "nanoagent framework")
    mm.get_store("cross_session").save_summarized_context("s1", "session summary " * 50)

    # 不同 token budget
    for budget in [500, 1000, 2000]:
        ctx = mm.build_context_for_prompt(max_tokens=budget)
        tokens_est = len(ctx) // 4
        print(f"Budget {budget} tokens → ~{tokens_est} chars, {len(ctx)} actual chars")

    # 优化器使用统计
    usage = optimizer.get_usage()
    print(f"\nToken usage by type: {usage}")


def demo_custom_store():
    """自定义 Store 演示。"""

    print("\n" + "=" * 60)
    print("自定义 Store")
    print("=" * 60)

    class RedisLikeStore(InMemoryStore):
        """模拟 Redis 的简单内存存储（实际上还是内存，但展示自定义扩展）。"""

        def __init__(self):
            super().__init__()
            self._ttl: dict[str, float] = {}

        def set_with_ttl(self, key: str, value: str, ttl_seconds: float) -> None:
            import time
            self.set(key, value)
            self._ttl[key] = time.time() + ttl_seconds

        def get_with_ttl(self, key: str, default=None):
            import time
            if key in self._ttl and time.time() > self._ttl[key]:
                self.delete(key)
                return default
            return self.get(key, default)

    mm = get_memory_manager()
    redis_store = RedisLikeStore()
    redis_store.set_with_ttl("temp_data", "expires in 5 seconds", ttl_seconds=5)
    redis_store.set("permanent_data", "this persists")

    print(f"\nTemp data (should exist): {redis_store.get_with_ttl('temp_data')}")
    print(f"Permanent data: {redis_store.get('permanent_data')}")

    # 热插拔到 memory manager
    mm.register_store("custom", redis_store)
    print(f"\nCustom store registered as 'custom' type: {mm.get_store('custom').memory_type}")


def demo_summarizer():
    """会话摘要器演示。"""
    print("\n" + "=" * 60)
    print("会话摘要器")
    print("=" * 60)

    from core.memory.summarizer import SessionSummarizer

    summarizer = SessionSummarizer()

    # 模拟一个会话
    session_id = summarizer.summarize_and_save(
        task="分析项目架构",
        tools_used=["read_file", "grep", "list_files"],
        artifacts=["架构图.png", "设计文档.md"],
        response="完成了架构分析，推荐使用模块化设计..."
    )

    print(f"\n保存的会话 ID: {session_id}")

    # 获取会话
    session = summarizer.get_session(session_id)
    if session:
        print(f"会话摘要: {session.get('summary', '')[:80]}...")

    # 搜索相关会话
    related = summarizer.find_related("架构", limit=5)
    print(f"相关会话数: {len(related)}")


def run_all_demos():
    """运行所有演示。"""
    reset_memory_manager()
    print("\n" + "=" * 60)
    print("NanoAgent Memory System Demo")
    print("=" * 60)

    demo_basic_operations()
    demo_hot_swap()
    demo_cross_session()
    demo_token_optimization()
    demo_custom_store()
    demo_summarizer()

    print("\n" + "=" * 60)
    print("所有演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_demos()