"""标记系统单元测试"""

from core.marker import (
    MarkerParser,
    MarkerBuilder,
    parse_markers,
    build_marker,
    MARKER_TYPES,
)


class TestMarkerParser:
    """测试标记解析器"""

    def test_parse_simple_marker(self):
        """测试解析简单标记"""
        text = "<|THINKING|>\n这是思考内容\n<|/THINKING|>"
        parser = MarkerParser()
        sections = parser.parse(text)

        assert len(sections) == 1
        assert sections[0].marker_type == "THINKING"
        assert sections[0].content == "这是思考内容"
        assert sections[0].metadata == {}

    def test_parse_marker_with_metadata(self):
        """测试解析带元数据的标记"""
        text = '<|TOOL|name="read_file" args=\'{"path": "/test.txt"}\'|>\n读取文件\n<|/TOOL|>'
        parser = MarkerParser()
        sections = parser.parse(text)

        assert len(sections) == 1
        assert sections[0].marker_type == "TOOL"
        assert sections[0].metadata["name"] == "read_file"
        assert sections[0].metadata["args"] == '{"path": "/test.txt"}'

    def test_parse_multiple_markers(self):
        """测试解析多个标记"""
        text = """<|THINKING|>
分析任务
<|/THINKING|>

<|PLAN|>
1. 第一步
2. 第二步
<|/PLAN|>

<|RESPONSE|>
完成
<|/RESPONSE|>"""

        parser = MarkerParser()
        sections = parser.parse(text)

        assert len(sections) == 3
        assert sections[0].marker_type == "THINKING"
        assert sections[1].marker_type == "PLAN"
        assert sections[2].marker_type == "RESPONSE"

    def test_extract_by_type(self):
        """测试按类型提取"""
        text = "<|THINKING|>思考1<|/THINKING|>\n<|PLAN|>计划1<|/PLAN|>\n<|THINKING|>思考2<|/THINKING|>"

        parser = MarkerParser()
        parser.parse(text)

        thinking_sections = parser.extract_by_type("THINKING")
        assert len(thinking_sections) == 2

        plan_sections = parser.extract_by_type("PLAN")
        assert len(plan_sections) == 1

    def test_extract_first(self):
        """测试提取第一个"""
        text = "<|THINKING|>思考1<|/THINKING|><|THINKING|>思考2<|/THINKING|>"
        parser = MarkerParser()
        parser.parse(text)

        first = parser.extract_first("THINKING")
        assert first is not None
        assert first.content == "思考1"

    def test_extract_first_not_found(self):
        """测试提取不存在的类型"""
        text = '<|THINKING|>思考<|/THINKING|>'
        parser = MarkerParser()
        parser.parse(text)

        first = parser.extract_first("PLAN")
        assert first is None

    def test_remove_markers(self):
        """测试移除标记"""
        text = "<|THINKING|>\n思考内容\n<|/THINKING|>"
        parser = MarkerParser()
        result = parser.remove_markers(text)

        assert result.strip() == "思考内容"

    def test_remove_markers_multiple(self):
        """测试移除多个标记"""
        text = "<|THINKING|>思考<|/THINKING|><|PLAN|>计划<|/PLAN|>"
        parser = MarkerParser()
        result = parser.remove_markers(text)

        assert result == "思考计划"

    def test_parse_empty_text(self):
        """测试解析空文本"""
        parser = MarkerParser()
        sections = parser.parse("")

        assert len(sections) == 0

    def test_parse_no_markers(self):
        """测试解析无标记的文本"""
        text = "普通文本，没有标记"
        parser = MarkerParser()
        sections = parser.parse(text)

        assert len(sections) == 0

    def test_parse_multiline_content(self):
        """测试解析多行内容"""
        text = """<|THINKING|>
第一行
第二行
第三行
<|/THINKING|>"""

        parser = MarkerParser()
        sections = parser.parse(text)

        assert len(sections) == 1
        assert "第一行" in sections[0].content
        assert "第二行" in sections[0].content
        assert "第三行" in sections[0].content


class TestMarkerBuilder:
    """测试标记构建器"""

    def test_build_simple_marker(self):
        """测试构建简单标记"""
        result = MarkerBuilder.build("THINKING", "思考内容")

        assert "<|THINKING|>" in result
        assert "<|/THINKING|>" in result
        assert "思考内容" in result

    def test_build_marker_with_metadata(self):
        """测试构建带元数据的标记"""
        result = MarkerBuilder.build(
            "TOOL", "工具调用", name="test_tool", arg1="value1"
        )

        assert '<|TOOL|name="test_tool" arg1="value1"|>' in result
        assert "工具调用" in result

    def test_thinking(self):
        """测试构建思考标记"""
        result = MarkerBuilder.thinking("思考过程")

        assert "<|THINKING|>" in result
        assert "思考过程" in result

    def test_plan(self):
        """测试构建计划标记"""
        result = MarkerBuilder.plan("执行计划")

        assert "<|PLAN|>" in result
        assert "执行计划" in result

    def test_tool(self):
        """测试构建工具标记"""
        args = {"path": "/test.txt", "mode": "read"}
        result = MarkerBuilder.tool("read_file", args, "读取文件")

        assert '<|TOOL|name="read_file"' in result
        assert "读取文件" in result
        assert '"path": "/test.txt"' in result

    def test_observation(self):
        """测试构建观察标记"""
        result = MarkerBuilder.observation("观察结果")

        assert "<|OBSERVATION|>" in result
        assert "观察结果" in result

    def test_reflection(self):
        """测试构建反思标记"""
        result = MarkerBuilder.reflection("反思内容")

        assert "<|REFLECTION|>" in result
        assert "反思内容" in result

    def test_response(self):
        """测试构建响应标记"""
        result = MarkerBuilder.response("响应内容")

        assert "<|RESPONSE|>" in result
        assert "响应内容" in result


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_parse_markers_convenience(self):
        """测试便捷解析函数"""
        text = "<|THINKING|>思考<|/THINKING|>"
        sections = parse_markers(text)

        assert len(sections) == 1
        assert sections[0].marker_type == "THINKING"

    def test_build_marker_convenience(self):
        """测试便捷构建函数"""
        result = build_marker("PLAN", "计划")

        assert "<|PLAN|>" in result
        assert "计划" in result


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流：构建 -> 解析 -> 提取"""
        # 构建标记
        text = MarkerBuilder.thinking("分析任务")
        text += MarkerBuilder.plan("执行计划")
        text += MarkerBuilder.tool("test_tool", {"arg": "value"}, "工具调用")

        # 解析
        parser = MarkerParser()
        sections = parser.parse(text)

        # 验证
        assert len(sections) == 3
        assert parser.extract_first("THINKING").content == "分析任务"
        assert parser.extract_first("PLAN").content == "执行计划"
        assert parser.extract_first("TOOL").metadata["name"] == "test_tool"

    def test_round_trip(self):
        """测试往返：构建 -> 解析 -> 重新构建"""
        original = MarkerBuilder.tool("read_file", {"path": "test.txt"}, "读取文件")

        parser = MarkerParser()
        sections = parser.parse(original)

        assert len(sections) == 1
        section = sections[0]

        # 重新构建
        rebuilt = MarkerBuilder.build(
            section.marker_type, section.content, **section.metadata
        )

        assert section.metadata["name"] in rebuilt
        assert section.content in rebuilt

    def test_complex_scenario(self):
        """测试复杂场景：完整的Agent思考流程"""
        workflow = MarkerBuilder.thinking("用户要求读取文件并分析内容")
        workflow += MarkerBuilder.plan("1. 读取文件\n2. 分析内容\n3. 返回结果")
        workflow += MarkerBuilder.tool(
            "read_file", {"path": "data.txt"}, "读取数据文件"
        )
        workflow += MarkerBuilder.observation("文件读取成功，内容为：...")
        workflow += MarkerBuilder.reflection("内容分析完成")
        workflow += MarkerBuilder.response("分析完成，文件包含X条记录")

        parser = MarkerParser()
        sections = parser.parse(workflow)

        assert len(sections) == 6
        assert sections[0].marker_type == "THINKING"
        assert sections[1].marker_type == "PLAN"
        assert sections[2].marker_type == "TOOL"
        assert sections[3].marker_type == "OBSERVATION"
        assert sections[4].marker_type == "REFLECTION"
        assert sections[5].marker_type == "RESPONSE"


class TestMarkerTypes:
    """测试标记类型定义"""

    def test_marker_types_defined(self):
        """测试所有标记类型已定义"""
        expected_types = [
            "THINKING",
            "PLAN",
            "TOOL",
            "OBSERVATION",
            "REFLECTION",
            "RESPONSE",
        ]
        for mtype in expected_types:
            assert mtype in MARKER_TYPES

    def test_marker_types_have_descriptions(self):
        """测试所有标记类型都有描述"""
        for mtype, desc in MARKER_TYPES.items():
            assert isinstance(desc, str)
            assert len(desc) > 0


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_content(self):
        """测试空内容"""
        text = "<|THINKING|>\n\n<|/THINKING|>"
        parser = MarkerParser()
        sections = parser.parse(text)

        assert len(sections) == 1
        assert sections[0].content == ""

    def test_special_characters_in_content(self):
        """测试内容中的特殊字符"""
        content = "包含 < > & \" ' 等特殊字符"
        result = MarkerBuilder.build("THINKING", content)
        parser = MarkerParser()
        sections = parser.parse(result)

        assert len(sections) == 1
        assert sections[0].content == content

    def test_very_long_content(self):
        """测试超长内容"""
        content = "A" * 10000
        result = MarkerBuilder.build("THINKING", content)
        parser = MarkerParser()
        sections = parser.parse(result)

        assert len(sections) == 1
        assert len(sections[0].content) == 10000

    def test_nested_markers_not_supported(self):
        """测试嵌套标记（不支持）"""
        text = "<|THINKING|>外层<|PLAN|>内层<|/PLAN|><|/THINKING|>"
        parser = MarkerParser()
        sections = parser.parse(text)

        # 应该只解析到第一层
        assert len(sections) == 1
        assert sections[0].marker_type == "THINKING"

    def test_unicode_content(self):
        """测试Unicode内容"""
        content = "中文 🎉 emoji 测试"
        result = MarkerBuilder.build("RESPONSE", content)
        parser = MarkerParser()
        sections = parser.parse(result)

        assert len(sections) == 1
        assert sections[0].content == content

    def test_multiple_metadata_attributes(self):
        """测试多个元数据属性"""
        result = MarkerBuilder.build(
            "TOOL",
            "调用",
            name="test_tool",
            arg1="value1",
            arg2="value2",
            arg3="value3",
        )
        parser = MarkerParser()
        sections = parser.parse(result)

        assert len(sections) == 1
        assert sections[0].metadata["name"] == "test_tool"
        assert sections[0].metadata["arg1"] == "value1"
        assert sections[0].metadata["arg2"] == "value2"
        assert sections[0].metadata["arg3"] == "value3"
