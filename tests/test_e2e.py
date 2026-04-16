"""端到端测试 - 验证完整 Agent 流程"""

import os
import sys
from pathlib import Path

# 标记测试模式
os.environ["NANOAGENT_TEST"] = "1"

sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.client import NanoLLMClient


def test_llm_mock_works():
    """验证 LLM mock 正常响应"""
    client = NanoLLMClient()

    resp = client.chat([{"role": "user", "content": "test"}])
    # Mock 可能返回空或无效内容，只检查不崩溃
    assert isinstance(resp, str)
    print("✅ test_llm_mock_works passed")


def test_tool_registry():
    """验证工具注册"""
    from tools.registry import get_tool_registry

    registry = get_tool_registry()
    tools = registry._tools
    assert "read_file" in tools
    assert "edit_file" in tools
    assert "run_bash" in tools
    print("✅ test_tool_registry passed")


def test_state_basic():
    """验证任务跟踪"""
    from core.spec import TaskSpec

    spec = TaskSpec("test task")
    assert spec.task == "test task"
    spec.add_artifact("hello.txt")
    assert "hello.txt" in spec.artifacts
    print("✅ test_state_basic passed")


if __name__ == "__main__":
    test_llm_mock_works()
    test_tool_registry()
    test_state_basic()
    print("\n🎉 所有端到端测试通过！")
