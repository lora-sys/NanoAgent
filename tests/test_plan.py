"""测试规划工具"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestExtractJson:
    """测试 JSON 解析辅助函数"""

    def test_extract_json_basic(self):
        from tools.plan import _extract_json

        text = '{"steps": [{"step": 1}], "total": 1}'
        result = _extract_json(text)
        assert result["total"] == 1
        assert len(result["steps"]) == 1

    def test_extract_json_with_prefix_suffix(self):
        from tools.plan import _extract_json

        text = 'Here is the plan:\n{"steps": [{"step": 1}], "total_steps": 1}\nDone.'
        result = _extract_json(text)
        assert result["total_steps"] == 1

    def test_extract_json_invalid(self):
        from tools.plan import _extract_json

        with pytest.raises(ValueError):
            _extract_json("no json here")


class TestPlanTool:
    """测试规划工具"""

    def _make_mock_module(self, response_or_error):
        """创建一个 mock llm.client 模块"""
        if isinstance(response_or_error, Exception):

            class FailLLM:
                def __init__(self):
                    pass

                def chat(self, msgs):
                    raise response_or_error

            MockClass = FailLLM
        else:

            class MockLLM:
                def __init__(self):
                    pass

                def chat(self, msgs):
                    return response_or_error

            MockClass = MockLLM

        mock_mod = type("MockLLMClientModule", (), {"NanoLLMClient": MockClass})()
        return mock_mod

    def test_plan_returns_structure(self, monkeypatch):
        """测试 plan 返回正确的结构"""
        mock_response = """{
  "steps": [
    {
      "step": 1,
      "description": "Read project structure",
      "reasoning": "Need to understand codebase first",
      "complexity": "低"
    }
  ],
  "total_steps": 1,
  "reasoning": "Start by understanding the project",
  "estimated_difficulty": "低",
  "potential_risks": []
}"""
        mock_module = self._make_mock_module(mock_response)
        monkeypatch.setitem(sys.modules, "llm.client", mock_module)

        from tools.plan import plan

        result = plan("分析这个项目")

        assert "plan_id" in result
        assert "steps" in result
        assert result["total_steps"] == 1
        assert len(result["steps"]) == 1
        assert result["steps"][0]["step"] == 1
        assert result["steps"][0]["description"] == "Read project structure"
        assert result["estimated_difficulty"] == "低"

    def test_plan_with_current_state(self, monkeypatch):
        """测试带当前状态的规划"""
        mock_response = '{"steps": [{"step": 1, "description": "Continue analysis", "reasoning": "Given current state", "complexity": "低"}], "total_steps": 1, "reasoning": "resume from current", "estimated_difficulty": "低", "potential_risks": []}'
        mock_module = self._make_mock_module(mock_response)
        monkeypatch.setitem(sys.modules, "llm.client", mock_module)

        from tools.plan import plan

        result = plan(
            goal="完成项目分析",
            current_state={"files_analyzed": ["README.md", "core/agent.py"]},
        )

        assert result["total_steps"] == 1

    def test_plan_with_constraints(self, monkeypatch):
        """测试带约束条件的规划"""
        mock_response = '{"steps": [{"step": 1, "description": "Plan with constraints", "reasoning": "Applied", "complexity": "中"}], "total_steps": 1, "reasoning": "test", "estimated_difficulty": "中", "potential_risks": []}'
        mock_module = self._make_mock_module(mock_response)
        monkeypatch.setitem(sys.modules, "llm.client", mock_module)

        from tools.plan import plan

        result = plan(
            goal="重构代码",
            constraints=["必须保持向后兼容", "不超过5步"],
        )

        assert result["total_steps"] == 1

    def test_plan_llm_error(self, monkeypatch):
        """测试 LLM 调用失败时的处理"""
        mock_module = self._make_mock_module(RuntimeError("LLM unavailable"))
        monkeypatch.setitem(sys.modules, "llm.client", mock_module)

        from tools.plan import plan

        result = plan("分析项目")
        assert "error" in result
        assert "LLM" in result["error"]
        assert result["total_steps"] == 0
        assert "plan_id" in result

    def test_plan_invalid_json_response(self, monkeypatch):
        """测试 LLM 返回无效 JSON 时的处理"""
        mock_module = self._make_mock_module("This is not JSON at all")
        monkeypatch.setitem(sys.modules, "llm.client", mock_module)

        from tools.plan import plan

        result = plan("分析项目")
        assert "error" in result
        assert "解析" in result["error"]


class TestPlanToolRegistration:
    """测试规划工具注册"""

    def test_plan_registered_in_registry(self):
        """验证 plan 工具已注册"""
        # 需要清除已有的 registry 单例以获取最新的
        import tools.registry as registry_module

        registry_module._registry = None
        reg = registry_module.get_tool_registry()

        tool_names = list(reg._tools.keys())
        assert "plan" in tool_names
        assert "read_file" in tool_names
        assert "list_files" in tool_names

    def test_plan_tool_in_tool_list(self):
        """验证 plan 工具在工具列表中"""
        import tools.registry as registry_module

        registry_module._registry = None
        reg = registry_module.get_tool_registry()

        tool_list = reg.get_tool_list()
        plan_tool = next((t for t in tool_list if t["function"]["name"] == "plan"), None)
        assert plan_tool is not None
        assert "goal" in plan_tool["function"]["parameters"]["properties"]
        assert "current_state" in plan_tool["function"]["parameters"]["properties"]
        assert "constraints" in plan_tool["function"]["parameters"]["properties"]

    def test_plan_tool_executable(self, monkeypatch):
        """测试通过 registry 执行 plan 工具"""
        mock_response = '{"steps": [{"step": 1, "description": "Test step", "reasoning": "Test", "complexity": "低"}], "total_steps": 1, "reasoning": "Test", "estimated_difficulty": "低", "potential_risks": []}'

        class MockLLM:
            def __init__(self):
                pass

            def chat(self, msgs):
                return mock_response

        mock_module = type("MockLLMClientModule", (), {"NanoLLMClient": MockLLM})()
        monkeypatch.setitem(sys.modules, "llm.client", mock_module)

        import tools.registry as registry_module

        registry_module._registry = None
        reg = registry_module.get_tool_registry()

        result = reg.execute("plan", {"goal": "测试目标"})
        assert "plan_id" in result
        assert "steps" in result
        assert result["total_steps"] == 1


class TestPlanSchema:
    """测试规划工具的 schema"""

    def test_plan_schema_goal_required(self):
        """验证 goal 是必需参数"""
        import tools.registry as registry_module

        registry_module._registry = None
        reg = registry_module.get_tool_registry()

        tool = reg._tools["plan"]
        required = tool["schema"]["required"]
        assert "goal" in required

    def test_plan_schema_optional_params(self):
        """验证 current_state 和 constraints 是可选参数"""
        import tools.registry as registry_module

        registry_module._registry = None
        reg = registry_module.get_tool_registry()

        tool = reg._tools["plan"]
        props = tool["schema"]["properties"]
        assert "goal" in props
        assert "current_state" in props
        assert "constraints" in props
        assert "default" in props["current_state"]
        assert props["current_state"]["default"] is None
