"""测试 NanoAgent 框架核心功能"""

import pytest
from core.agent import NanoAgent
from tools.registry import get_tool_registry


def test_agent_initialization():
    """测试 Agent 初始化"""
    agent = NanoAgent()
    assert agent.llm is not None
    assert agent.tools is not None
    assert agent.conversation == []


def test_tool_registration():
    """测试工具注册"""
    registry = get_tool_registry()
    tool_names = [tool["name"] for tool in registry.get_tool_list()]
    
    # 验证内置工具存在
    assert "read_file" in tool_names
    assert "list_files" in tool_names
    assert "edit_file" in tool_names
    assert "run_bash" in tool_names


def test_tool_execution():
    """测试工具执行"""
    registry = get_tool_registry()
    
    # 测试 read_file 工具
    result = registry.execute("read_file", {"filename": "README.md"})
    assert "file_path" in result
    assert "content" in result
    
    # 测试 list_files 工具
    result = registry.execute("list_files", {"path": "."})
    assert "path" in result
    assert "files" in result


def test_spec_tracking():
    """测试任务跟踪"""
    from core.spec import TaskSpec
    
    spec = TaskSpec("测试任务")
    spec.add_tool_call("read_file")
    spec.add_artifact("README.md")
    spec.add_decision("使用 read_file 工具")
    spec.complete()
    
    assert spec.status == "completed"
    assert spec.steps_executed == 1
    assert "read_file" in spec.tools_used
    assert "README.md" in spec.artifacts


def test_config_loading():
    """测试配置加载"""
    from config import get_config
    
    config = get_config()
    assert "llm" in config
    assert "model" in config["llm"]


def test_system_prompt_generation():
    """测试系统提示生成"""
    agent = NanoAgent()
    prompt = agent._get_system_prompt()
    
    assert "工具" in prompt
    assert "tool:" in prompt
    assert "read_file" in prompt
    assert "run_bash" in prompt


if __name__ == "__main__":
    # 快速测试
    test_agent_initialization()
    test_tool_registration()
    test_tool_execution()
    test_spec_tracking()
    test_config_loading()
    test_system_prompt_generation()
    print("✅ 所有测试通过！")