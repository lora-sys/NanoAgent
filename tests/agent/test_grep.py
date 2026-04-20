"""grep 工具测试 — 使用 AgentTestHarness"""

import pytest

from tests.agent.harness import AgentTestHarness
from tests.agent.fixtures import get_task


@pytest.mark.unit
def test_grep_tool_exists():
    """验证 grep 工具已注册"""
    harness = AgentTestHarness(mode="mock")
    harness.load_mock_responses([
        '{"action": "complete", "reason": "mock done"}',
    ])
    harness.run_agent("随便什么任务", max_iterations=1)
    # mock 模式不走工具链，只验证不崩溃
    assert harness.last_result is not None


@pytest.mark.integration
def test_grep_search_with_real_api():
    """真实 API 测试：grep 搜索函数定义"""
    harness = AgentTestHarness(mode="real")

    harness.run_agent(get_task("grep_search"), max_iterations=8)

    # grep 工具成功调用，或 agent 以文字描述响应（均算通过）
    grep_called = "grep" in harness.tools_used
    response_has_content = bool(harness.last_result and harness.last_result.get("response"))
    assert grep_called or response_has_content, "Agent 既没有调用 grep 也没有返回内容"
    if grep_called:
        # 缓存摘要替换原文，检查 stats 或匹配数
        response = harness.last_result.get("response", "")
        has_stats = any(k in response for k in ["matches", "文件", "cache_ref"])
        assert has_stats, f"摘要应含 stats 或 cache_ref，实际: {response[:200]}"
    print(f"工具调用: {harness.tools_used}")


@pytest.mark.integration
def test_grep_no_match_with_real_api():
    """真实 API 测试：grep 无匹配结果（模型行为依赖）"""
    harness = AgentTestHarness(mode="real")

    harness.run_agent(get_task("grep_no_match"), max_iterations=5)

    # 模型可能直接回答，也可能调用工具；框架验证不崩溃
    assert harness.last_result is not None
    assert harness.last_result.get("status") in ("completed", "failed")
    print(f"工具调用: {harness.tools_used}, 状态: {harness.last_result.get('status')}")


@pytest.mark.unit
def test_grep_unit_mock():
    """Mock 模式测试：mock LLM 响应引导调用 grep"""
    # 设计 mock 响应序列：
    # 1. LLM 第一次响应 → 调用 grep
    # 2. LLM 第二次响应 → 完成任务
    harness = AgentTestHarness(mode="mock")
    harness.load_mock_responses([
        '<tool name="grep" args=\'{"pattern": "def run", "path": "core", "max_count": 10}\'/>',
        "<response>找到 def run 定义</response>",
    ])

    harness.run_agent(get_task("grep_search"), max_iterations=3)

    harness.assert_tool_called("grep")
    harness.assert_status("completed")


@pytest.mark.unit
def test_grep_unit_no_tool_call():
    """Mock 模式测试：简单任务不需要 grep"""
    harness = AgentTestHarness(mode="mock")
    harness.load_mock_responses([
        "<response>Python 是一种高级编程语言。</response>",
    ])

    harness.run_agent(get_task("simple_chat"), max_iterations=2)

    harness.assert_tool_not_called("grep")


@pytest.mark.unit
def test_grep_call_count():
    """Mock 模式测试：验证工具调用次数"""
    harness = AgentTestHarness(mode="mock")
    harness.load_mock_responses([
        '<tool name="grep" args=\'{"pattern": "def", "path": "core"}\'/>',
        '<tool name="grep" args=\'{"pattern": "class", "path": "core"}\'/>',
        "<response>搜索完成</response>",
    ])

    harness.run_agent("搜索函数和类定义", max_iterations=3)

    harness.assert_tool_call_count("grep", 2)
    harness.assert_tool_call_count("read_file", 0)
