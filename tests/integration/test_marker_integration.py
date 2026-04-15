"""标记系统集成测试"""

import pytest
from unittest.mock import Mock, patch

from core.agent import NanoAgent
from core.marker import MarkerBuilder


class TestMarkerIntegration:
    """测试标记系统与 Agent 的集成"""

    @pytest.fixture
    def mock_llm_client(self):
        """模拟 LLM 客户端"""
        mock_client = Mock()
        return mock_client

    @pytest.fixture
    def mock_tools_registry(self):
        """模拟工具注册表"""
        mock_registry = Mock()
        mock_registry.get_tool_descriptions.return_value = (
            "read_file: 读取文件\nwrite_file: 写入文件"
        )
        mock_registry.execute = Mock(return_value="执行成功")
        return mock_registry

    def test_parse_marker_response_with_thinking(self):
        """测试解析包含思考的标记响应"""
        response = """<|THINKING|>
我需要读取文件来完成任务
<|/THINKING|>

<|TOOL|name='read_file' args='{"path": "/test.txt"}'|>
读取文件内容
<|/TOOL|>"""

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        assert result["action"] == "tool_call"
        assert result["tool"] == "read_file"
        assert result["arguments"] == {"path": "/test.txt"}
        assert "读取文件" in result["thinking"]

    def test_parse_marker_response_with_plan(self):
        """测试解析包含计划的标记响应"""
        response = """<|PLAN|>
1. 读取文件
2. 分析内容
3. 生成结果
<|/PLAN|>

<|TOOL|name='read_file' args='{"path": "/test.txt"}'|>
读取文件
<|/TOOL|>"""

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        assert result["action"] == "tool_call"
        assert "读取文件" in result["plan"]

    def test_parse_marker_response_with_observation(self):
        """测试解析包含观察的标记响应"""
        response = """<|OBSERVATION|>
文件读取成功，内容为：Hello World
<|/OBSERVATION|>

<|REFLECTION|>
内容分析完成
<|/REFLECTION|>

<|RESPONSE|>
任务完成
<|/RESPONSE|>"""

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        assert result["action"] == "complete"
        assert "文件读取成功" in result["observation"]
        assert "内容分析完成" in result["reflection"]
        assert "任务完成" in result["reason"]

    def test_parse_marker_response_complete(self):
        """测试解析完成的标记响应"""
        response = """<|THINKING|>
所有任务已完成
<|/THINKING|>

<|RESPONSE|>
任务完成，所有需求都已满足
<|/RESPONSE|>"""

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        assert result["action"] == "complete"
        assert "任务完成" in result["reason"]

    def test_parse_marker_response_wait(self):
        """测试解析等待的标记响应"""
        response = """<|RESPONSE|>
等待用户输入更多信息
<|/RESPONSE|>"""

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        assert result["action"] == "wait"
        assert "等待" in result["reason"]

    def test_parse_marker_response_invalid(self):
        """测试解析无效的标记响应"""
        response = "这不是有效的标记格式"

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        assert result["action"] == "wait"
        assert "无法解析" in result["reason"]

    def test_parse_marker_response_full_workflow(self):
        """测试完整工作流的标记响应"""
        response = """<|THINKING|>
用户要求读取并分析文件
<|/THINKING|>

<|PLAN|>
1. 读取文件
2. 分析内容
3. 返回结果
<|/PLAN|>

<|TOOL|name='read_file' args='{"path": "/data.txt"}'|>
读取数据文件
<|/TOOL|>"""

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        assert result["action"] == "tool_call"
        assert result["tool"] == "read_file"
        assert "读取并分析文件" in result["thinking"]
        assert "读取文件" in result["plan"]

    def test_parse_marker_response_tool_with_complex_args(self):
        """测试解析复杂工具参数的标记响应"""
        response = """<|THINKING|>
需要执行复杂的文件操作
<|/THINKING|>

<|TOOL|name='write_file' args='{"path": "/output.txt", "content": "Hello World", "mode": "overwrite"}'|>
写入文件
<|/TOOL|>"""

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        assert result["action"] == "tool_call"
        assert result["tool"] == "write_file"
        assert result["arguments"]["path"] == "/output.txt"
        assert result["arguments"]["content"] == "Hello World"
        assert result["arguments"]["mode"] == "overwrite"

    def test_parse_marker_response_multiple_tools(self):
        """测试解析多个工具调用的标记响应"""
        # 注意：当前实现只解析第一个工具调用
        response = """<|THINKING|>
需要读取两个文件
<|/THINKING|>

<|TOOL|name='read_file' args='{"path": "/file1.txt"}'|>
读取第一个文件
<|/TOOL|>

<|OBSERVATION|>
第一个文件读取成功
<|/OBSERVATION|>"""

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        assert result["action"] == "tool_call"
        assert result["tool"] == "read_file"
        assert result["arguments"]["path"] == "/file1.txt"

    def test_parse_marker_response_with_reflection(self):
        """测试解析包含反思的标记响应"""
        response = """<|OBSERVATION|>
工具执行成功，结果为...
<|/OBSERVATION|>

<|REFLECTION|>
执行结果符合预期，可以继续下一步
<|/REFLECTION|>

<|RESPONSE|>
任务完成
<|/RESPONSE|>"""

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        assert result["action"] == "complete"
        assert "工具执行成功" in result["observation"]
        assert "符合预期" in result["reflection"]
        assert "任务完成" in result["reason"]

    def test_build_and_parse_roundtrip(self):
        """测试构建和解析的往返测试"""
        original = (
            MarkerBuilder.thinking("分析任务")
            + MarkerBuilder.plan("执行计划")
            + MarkerBuilder.tool("test_tool", {"arg": "value"}, "工具调用")
        )

        agent = NanoAgent()
        result = agent._parse_marker_response(original)

        assert "分析任务" in result.get("thinking", "")
        assert "执行计划" in result.get("plan", "")
        assert result["action"] == "tool_call"
        assert result["tool"] == "test_tool"


class TestMarkerInAgentWorkflow:
    """测试标记系统在 Agent 工作流中的使用"""

    def test_system_prompt_uses_markers(self):
        """测试系统提示词使用标记格式"""
        agent = NanoAgent()
        prompt = agent._system_prompt()

        assert "THINKING" in prompt
        assert "PLAN" in prompt
        assert "TOOL" in prompt
        assert "OBSERVATION" in prompt
        assert "REFLECTION" in prompt
        assert "RESPONSE" in prompt

    def test_build_think_prompt_uses_markers(self):
        """测试构建思考提示词使用标记格式"""
        agent = NanoAgent()
        agent.state.update_spec({"task": "测试任务"})
        prompt = agent._build_think_prompt()

        assert "THINKING" in prompt
        assert "TOOL" in prompt

    @patch("core.agent.NanoLLMClient")
    def test_think_method_returns_parsed_markers(self, mock_llm_class):
        """测试 think 方法返回解析后的标记"""
        mock_llm = Mock()
        mock_llm.chat.return_value = """<|THINKING|>
思考过程
<|/THINKING|>

<|TOOL|name='test_tool' args='{"arg": "value"}'|>
工具调用
<|/TOOL|>"""
        mock_llm_class.return_value = mock_llm

        agent = NanoAgent()
        result = agent._think()

        assert result["action"] == "tool_call"
        assert result["tool"] == "test_tool"
        assert "思考过程" in result["thinking"]

    def test_cli_display_marker(self):
        """测试 CLI 显示标记"""
        from core.agent import NanoAgent

        cli = NanoAgent._get_cli()

        # 测试不同类型的标记显示
        marker_types = [
            "THINKING",
            "PLAN",
            "TOOL",
            "OBSERVATION",
            "REFLECTION",
            "RESPONSE",
        ]

        for marker_type in marker_types:
            assert marker_type in cli.MARKER_STYLES
            assert "icon" in cli.MARKER_STYLES[marker_type]
            assert "color" in cli.MARKER_STYLES[marker_type]


class TestMarkerErrorHandling:
    """测试标记系统的错误处理"""

    def test_parse_malformed_marker(self):
        """测试解析格式错误的标记"""
        response = """<|THINKING|>
未闭合的标记
"""

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        assert result["action"] == "wait"

    def test_parse_invalid_json_in_tool_args(self):
        """测试解析工具参数中的无效 JSON"""
        response = """<|TOOL|name='test_tool' args='invalid json'|>
工具调用
<|/TOOL|>"""

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        assert result["action"] == "tool_call"
        assert result["tool"] == "test_tool"
        assert result["arguments"] == {}

    def test_parse_empty_response(self):
        """测试解析空响应"""
        response = ""

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        assert result["action"] == "wait"

    def test_parse_only_text_no_markers(self):
        """测试解析只有文本没有标记的响应"""
        response = "这是一段普通文本，没有任何标记"

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        assert result["action"] == "wait"

    def test_parse_marker_with_unicode(self):
        """测试解析包含 Unicode 字符的标记"""
        response = """<|THINKING|>
中文思考 🎉 emoji 测试
<|/THINKING|>

<|RESPONSE|>
任务完成 ✅
<|/RESPONSE|>"""

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        assert "中文思考" in result["thinking"]
        assert "任务完成" in result["reason"]
        assert result["action"] == "complete"


class TestMarkerPerformance:
    """测试标记系统的性能"""

    def test_parse_large_response(self):
        """测试解析大型响应"""
        # 构建一个包含大量标记的响应
        response_parts = []
        for i in range(10):
            response_parts.append(MarkerBuilder.thinking(f"思考过程 {i}"))
            response_parts.append(MarkerBuilder.plan(f"计划步骤 {i}"))

        response = "\n".join(response_parts)

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        # 应该能够解析出最后一个工具或响应
        assert result["action"] in ["tool_call", "complete", "wait"]

    def test_parse_nested_content(self):
        """测试解析嵌套内容的标记"""
        complex_content = """
        第一层内容
        第二层内容
        {
            "nested": "data"
        }
        """

        response = MarkerBuilder.thinking(complex_content)

        agent = NanoAgent()
        result = agent._parse_marker_response(response)

        assert "第一层内容" in result["thinking"]
        assert "第二层内容" in result["thinking"]
