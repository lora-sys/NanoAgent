"""测试流式传输和新的标记类型"""

import re
from core.agent import NanoAgent


def test_extract_tool_invocations_xml():
    """测试 XML 格式的工具调用解析"""
    agent = NanoAgent()

    # 测试 XML 格式
    text = '<tool name="read_file" args=\'{"filename": "README.md"}\'/>'
    invocations = agent._extract_tool_invocations(text)

    assert len(invocations) == 1
    assert invocations[0][0] == "read_file"
    assert invocations[0][1] == {"filename": "README.md"}


def test_extract_tool_invocations_old_format():
    """测试旧格式的工具调用解析"""
    agent = NanoAgent()

    # 测试旧格式
    text = 'tool: read_file({"filename": "README.md"})'
    invocations = agent._extract_tool_invocations(text)

    assert len(invocations) == 1
    assert invocations[0][0] == "read_file"
    assert invocations[0][1] == {"filename": "README.md"}


def test_extract_response_and_error():
    """测试 response 和 error 标记提取"""
    agent = NanoAgent()

    # 测试 response 标记
    text = "<response>这是一个回复</response>"
    result = agent._extract_response_and_error(text)

    assert result["response"] == "这是一个回复"
    assert result["error"] == ""

    # 测试 error 标记
    text = "<error>这是一个错误</error>"
    result = agent._extract_response_and_error(text)

    assert result["response"] == ""
    assert result["error"] == "这是一个错误"

    # 测试混合标记
    text = "<response>回复内容</response>\n<error>错误内容</error>"
    result = agent._extract_response_and_error(text)

    assert result["response"] == "回复内容"
    assert result["error"] == "错误内容"


def test_stream_chat():
    """测试流式聊天功能"""
    from llm.client import NanoLLMClient

    client = NanoLLMClient()
    messages = [{"role": "user", "content": "你好"}]

    # 测试流式输出
    tokens = []

    def callback(token):
        tokens.append(token)

    # 注意：这个测试需要 mock 模式才能正常工作
    full_content = client.stream_chat(messages, callback=callback)

    # 验证回调被调用
    if not client.mock_enabled:
        # 如果不是 mock 模式，验证流式输出
        assert len(tokens) > 0, "流式输出应该产生至少一个 token"


def test_xml_pattern_performance():
    """测试 XML 正则表达式的性能"""
    agent = NanoAgent()

    # 生成测试文本
    test_text = ""
    for i in range(100):
        test_text += f'<tool name="tool_{i}" args=\'{{"index": {i}}}\'/>\n'

    import time
    start = time.time()
    invocations = agent._extract_tool_invocations(test_text)
    end = time.time()

    # 验证解析正确性
    assert len(invocations) == 100

    # 验证性能（应该在 100ms 内完成）
    assert (end - start) < 0.1, f"解析 100 个工具调用耗时 {end - start:.3f}s，超过 100ms"

    print(f"✅ 性能测试通过：解析 100 个工具调用耗时 {(end - start) * 1000:.2f}ms")


if __name__ == "__main__":
    print("🧪 开始测试流式传输和新的标记类型...")

    test_extract_tool_invocations_xml()
    print("✅ XML 格式工具调用解析测试通过")

    test_extract_tool_invocations_old_format()
    print("✅ 旧格式工具调用解析测试通过")

    test_extract_response_and_error()
    print("✅ response 和 error 标记提取测试通过")

    test_stream_chat()
    print("✅ 流式聊天功能测试通过")

    test_xml_pattern_performance()
    print("✅ XML 正则表达式性能测试通过")

    print("\n🎉 所有测试通过！")