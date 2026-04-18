"""Test plan tool."""

import json
import pytest
import sys
import tempfile
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def clean_todo_file(monkeypatch):
    """Use a temp file for todo persistence during plan tests."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp = Path(f.name)
    monkeypatch.setattr("tools.todo.TODO_FILE", tmp)
    yield tmp
    if tmp.exists():
        tmp.unlink()


class TestExtractJson:
    """测试 JSON 解析（复用 core.utils 的逻辑）"""

    def test_extract_json_basic(self):
        from core.utils import extract_json

        text = '{"steps": [{"step": 1}], "total": 1}'
        result = extract_json(text)
        assert result["total"] == 1
        assert len(result["steps"]) == 1

    def test_extract_json_with_prefix_suffix(self):
        from core.utils import extract_json

        text = 'Here is the plan:\n{"steps": [{"step": 1}], "total_steps": 1}\nDone.'
        result = extract_json(text)
        assert result["total_steps"] == 1

    def test_extract_json_markdown_code_block(self):
        from core.utils import extract_json

        text = '```json\n{"steps": [{"step": 1}], "total_steps": 1}\n```'
        result = extract_json(text)
        assert result["total_steps"] == 1

    def test_extract_json_invalid(self):
        from core.utils import extract_json

        with pytest.raises(json.JSONDecodeError):
            extract_json("no json here")


class _MockLLM:
    def __init__(self, response_or_error):
        self._response = response_or_error
        self.last_msgs = None

    def chat(self, msgs):
        self.last_msgs = msgs
        if isinstance(self._response, Exception):
            raise self._response
        return self._response

    async def achat(self, msgs):
        self.last_msgs = msgs
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


def _patch_llm(monkeypatch, response_or_error):
    mock = _MockLLM(response_or_error)

    class MockNanoLLMClient:
        _mock = mock

        def __init__(self, model=None):
            self._mock = mock

        def chat(self, msgs):
            return self._mock.chat(msgs)

        async def achat(self, msgs):
            return await self._mock.achat(msgs)

    class MockModule:
        NanoLLMClient = MockNanoLLMClient

    monkeypatch.setitem(sys.modules, "llm.client", MockModule())
    # 清除 plan.py 的缓存 client
    import tools.plan as plan_module

    monkeypatch.setattr(plan_module, "_llm_client", None)
    return mock


class TestPlanInputValidation:
    """测试输入验证"""

    def test_empty_goal(self, monkeypatch):
        _patch_llm(monkeypatch, "unexpected")
        from tools.plan import plan

        result = plan("")
        assert "error" in result
        assert "empty" in result["error"]
        assert result["total_steps"] == 0

    def test_whitespace_goal(self, monkeypatch):
        _patch_llm(monkeypatch, "unexpected")
        from tools.plan import plan

        result = plan("   ")
        assert "error" in result
        assert "empty" in result["error"]

    def test_invalid_current_state_type(self, monkeypatch):
        _patch_llm(monkeypatch, "unexpected")
        from tools.plan import plan

        result = plan("分析项目", current_state="not a dict")
        assert "error" in result
        assert "current_state" in result["error"]
        assert result["total_steps"] == 0

    def test_invalid_constraints_type(self, monkeypatch):
        _patch_llm(monkeypatch, "unexpected")
        from tools.plan import plan

        result = plan("分析项目", constraints="not a list")
        assert "error" in result
        assert "constraints" in result["error"]
        assert result["total_steps"] == 0


class TestPlanLLMIntegration:
    """测试 LLM 集成"""

    def test_plan_returns_structure(self, monkeypatch):
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
        _patch_llm(monkeypatch, mock_response)
        from tools.plan import plan

        result = plan("分析这个项目")

        assert "plan_id" in result
        assert "steps" in result
        assert result["total_steps"] == 1
        assert len(result["steps"]) == 1
        assert result["steps"][0]["description"] == "Read project structure"
        assert "todo_id" in result

    def test_plan_with_current_state(self, monkeypatch):
        mock_response = '{"steps": [{"step": 1, "description": "Continue", "reasoning": "ok", "complexity": "低"}], "total_steps": 1, "reasoning": "test", "estimated_difficulty": "低", "potential_risks": []}'
        _patch_llm(monkeypatch, mock_response)
        from tools.plan import plan

        result = plan(
            "完成项目分析",
            current_state={"files_analyzed": ["README.md"]},
        )

        assert result["total_steps"] == 1

    def test_plan_with_constraints(self, monkeypatch):
        mock_response = '{"steps": [{"step": 1, "description": "Plan with constraints", "reasoning": "ok", "complexity": "中"}], "total_steps": 1, "reasoning": "test", "estimated_difficulty": "中", "potential_risks": []}'
        _patch_llm(monkeypatch, mock_response)
        from tools.plan import plan

        result = plan("重构代码", constraints=["保持兼容"])
        assert result["total_steps"] == 1

    def test_plan_llm_error(self, monkeypatch):
        _patch_llm(monkeypatch, RuntimeError("LLM unavailable"))
        from tools.plan import plan

        result = plan("分析项目")
        assert "error" in result
        assert "LLM" in result["error"]
        assert result["total_steps"] == 0

    def test_plan_invalid_json_response(self, monkeypatch):
        _patch_llm(monkeypatch, "This is not JSON at all")
        from tools.plan import plan

        result = plan("分析项目")
        assert "error" in result
        assert "解析" in result["error"]

    def test_plan_response_missing_steps_field(self, monkeypatch):
        """LLM 返回有效 JSON 但缺少 steps 字段"""
        mock_response = '{"total_steps": 5, "reasoning": "test"}'
        _patch_llm(monkeypatch, mock_response)
        from tools.plan import plan

        result = plan("分析项目")
        assert "steps" in result
        assert result["steps"] == []
        assert result["total_steps"] == 0

    def test_plan_response_steps_not_list(self, monkeypatch):
        """LLM 返回有效 JSON 但 steps 不是列表"""
        mock_response = '{"steps": "not a list", "total_steps": 0}'
        _patch_llm(monkeypatch, mock_response)
        from tools.plan import plan

        result = plan("分析项目")
        assert "steps" in result
        assert result["steps"] == []

    def test_plan_response_in_markdown(self, monkeypatch):
        """LLM 返回 markdown 代码块包裹的 JSON"""
        mock_response = """以下是计划:\n```json\n{"steps": [{"step": 1, "description": "First", "reasoning": "ok", "complexity": "低"}], "total_steps": 1, "reasoning": "test", "estimated_difficulty": "低", "potential_risks": []}\n```\n完成"""
        _patch_llm(monkeypatch, mock_response)
        from tools.plan import plan

        result = plan("分析项目")
        assert result["total_steps"] == 1
        assert result["steps"][0]["description"] == "First"


class TestPlanAsync:
    """Test async version."""

    @pytest.mark.asyncio
    async def test_aplan_returns_structure(self, monkeypatch):
        mock_response = '{"steps": [{"step": 1, "description": "Async step", "reasoning": "ok", "complexity": "低"}], "total_steps": 1, "reasoning": "test", "estimated_difficulty": "低", "potential_risks": []}'
        _patch_llm(monkeypatch, mock_response)
        from tools.plan import aplan

        result = await aplan("异步规划测试")

        assert "plan_id" in result
        assert result["total_steps"] == 1
        assert result["steps"][0]["description"] == "Async step"
        assert "todo_id" in result

    @pytest.mark.asyncio
    async def test_aplan_input_validation(self, monkeypatch):
        _patch_llm(monkeypatch, "unexpected")
        from tools.plan import aplan

        result = await aplan("")
        assert "error" in result
        assert "empty" in result["error"]

    @pytest.mark.asyncio
    async def test_aplan_llm_error(self, monkeypatch):
        _patch_llm(monkeypatch, RuntimeError("async error"))
        from tools.plan import aplan

        result = await aplan("分析项目")
        assert "error" in result
        assert "LLM" in result["error"]


class TestPlanRegistration:
    """测试工具注册"""

    def test_plan_registered(self):
        import tools.registry as registry_module

        registry_module._registry = None
        reg = registry_module.get_tool_registry()
        assert "plan" in reg._tools

    def test_plan_tool_list(self):
        import tools.registry as registry_module

        registry_module._registry = None
        reg = registry_module.get_tool_registry()

        tool_list = reg.get_tool_list()
        plan_tool = next(
            (t for t in tool_list if t["function"]["name"] == "plan"), None
        )
        assert plan_tool is not None
        props = plan_tool["function"]["parameters"]["properties"]
        assert "goal" in props
        assert "current_state" in props
        assert "constraints" in props

    def test_plan_goal_required(self):
        import tools.registry as registry_module

        registry_module._registry = None
        reg = registry_module.get_tool_registry()

        tool = reg._tools["plan"]
        assert "goal" in tool["schema"]["required"]

    def test_plan_optional_defaults(self):
        import tools.registry as registry_module

        registry_module._registry = None
        reg = registry_module.get_tool_registry()

        props = reg._tools["plan"]["schema"]["properties"]
        assert props["current_state"]["default"] is None
        assert props["constraints"]["default"] is None
