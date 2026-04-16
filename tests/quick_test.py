"""快速测试 NanoAgent 框架"""

from core.agent import NanoAgent
from tools.registry import get_tool_registry
from core.spec import TaskSpec
from config import get_config


def test_agent_initialization():
    """测试 Agent 初始化"""
    print("\n1. 测试 Agent 初始化...")
    agent = NanoAgent()
    assert agent.llm is not None
    assert agent.tools is not None
    assert agent.conversation == []
    print("✅ Agent 初始化测试通过")


def test_tool_registration():
    """测试工具注册"""
    print("\n2. 测试工具注册...")
    registry = get_tool_registry()
    tool_list = registry.get_tool_list()
    tool_names = [tool["function"]["name"] for tool in tool_list]
    assert "read_file" in tool_names
    assert "list_files" in tool_names
    assert "edit_file" in tool_names
    assert "run_bash" in tool_names
    print(f"✅ 工具注册测试通过，工具: {tool_names}")


def test_tool_execution():
    """测试工具执行"""
    print("\n3. 测试工具执行...")
    registry = get_tool_registry()

    result = registry.execute("read_file", {"filename": "README.md"})
    assert "file_path" in result
    assert "content" in result
    print(f"✅ read_file 测试通过，文件路径: {result['file_path']}")

    result = registry.execute("list_files", {"path": "."})
    assert "path" in result
    assert "files" in result
    print(f"✅ list_files 测试通过，找到 {len(result['files'])} 个文件")


def test_task_tracking():
    """测试任务跟踪"""
    print("\n4. 测试任务跟踪...")
    spec = TaskSpec("测试任务")
    spec.add_tool_call("read_file")
    spec.add_artifact("README.md")
    spec.add_decision("使用 read_file 工具")
    spec.complete()
    assert spec.status == "completed"
    assert spec.steps_executed == 1
    assert "read_file" in spec.tools_used
    assert "README.md" in spec.artifacts
    print("✅ 任务跟踪测试通过")


def test_config_loading():
    """测试配置加载"""
    print("\n5. 测试配置加载...")
    config = get_config()
    assert "llm" in config
    assert "model" in config["llm"]
    print(f"✅ 配置加载测试通过，模型: {config['llm']['model']}")


def test_system_prompt_generation():
    """测试系统提示生成"""
    print("\n6. 测试系统提示生成...")
    agent = NanoAgent()
    prompt = agent._get_system_prompt()
    assert "工具" in prompt
    assert "tool:" in prompt
    assert "read_file" in prompt
    assert "run_bash" in prompt
    print("✅ 系统提示生成测试通过")


if __name__ == "__main__":
    print("🧪 开始测试 NanoAgent 框架...")

    test_agent_initialization()
    test_tool_registration()
    test_tool_execution()
    test_task_tracking()
    test_config_loading()
    test_system_prompt_generation()

    print("\n🎉 所有测试通过！NanoAgent 框架运行正常！")
    print("\n📊 框架特性:")
    print("  - 极简设计")
    print("  - 零魔法")
    print("  - 高性能")
    print("  - 易扩展")
    print("  - 灵活控制")
