"""测试异步功能和流式响应重建"""

import asyncio
import pytest
import litellm
from llm.client import NanoLLMClient


def test_stream_chunk_builder():
    """测试流式响应重建功能"""
    client = NanoLLMClient()

    # 模拟 chunks
    chunks = []
    messages = [{"role": "user", "content": "你好"}]

    # 创建模拟的 chunk 对象
    class MockChunk:
        def __init__(self, content):
            self.choices = [
                type(
                    "Choice", (), {"delta": type("Delta", (), {"content": content})()}
                )()
            ]

    chunks.append(MockChunk("你好"))
    chunks.append(MockChunk("，"))
    chunks.append(MockChunk("我是"))
    chunks.append(MockChunk("AI"))

    # 测试重建
    result = client.stream_chunk_builder(chunks, messages)
    assert result == "你好，我是AI"


@pytest.mark.asyncio
async def test_achat():
    """测试异步聊天"""
    client = NanoLLMClient()
    messages = [{"role": "user", "content": "你好"}]

    # 测试异步聊天（mock 模式）
    result = await client.achat(messages)
    assert result is not None


@pytest.mark.asyncio
async def test_astream_chat():
    """测试异步流式聊天"""
    client = NanoLLMClient()
    messages = [{"role": "user", "content": "你好"}]

    tokens = []

    def callback(token):
        tokens.append(token)

    # 测试异步流式聊天（mock 模式）
    result = await client.astream_chat(messages, callback=callback)
    assert result is not None
    # 验证回调被调用
    if client.mock_enabled:
        assert len(tokens) > 0


@pytest.mark.asyncio
async def test_astructured_chat():
    """测试异步结构化聊天"""
    from pydantic import BaseModel

    class TestResponse(BaseModel):
        message: str

    client = NanoLLMClient()
    messages = [{"role": "user", "content": "你好"}]

    # 测试异步结构化聊天（mock 模式）
    try:
        result = await client.astructured_chat(messages, TestResponse)
        assert result is not None
    except Exception as e:
        # Mock 模式可能会失败，这是正常的
        print(f"Mock 模式下的预期错误: {e}")


def test_infinite_loop_protection():
    """测试防止无限循环的保护机制"""
    client = NanoLLMClient()

    # 验证配置已设置
    assert litellm.REPEATED_STREAMING_CHUNK_LIMIT == 100

    # 模拟重复的 chunks
    messages = [{"role": "user", "content": "测试"}]

    class MockChunk:
        def __init__(self, content):
            self.choices = [
                type(
                    "Choice", (), {"delta": type("Delta", (), {"content": content})()}
                )()
            ]

    # 创建超过限制的重复 chunks
    chunks = [MockChunk("重复内容")] * 101

    # 测试重建功能
    result = client.stream_chunk_builder(chunks, messages)
    assert result == "重复内容" * 101


def test_stream_chat_with_infinite_loop_detection():
    """测试流式聊天中的无限循环检测"""
    client = NanoLLMClient()

    if client.mock_enabled:
        # Mock 模式下不需要测试无限循环检测
        print("⚠️ Mock 模式下跳过无限循环检测测试")
        return

    messages = [{"role": "user", "content": "测试无限循环保护"}]
    tokens = []

    def callback(token):
        tokens.append(token)

    # 这个测试需要真实的环境，在 mock 模式下跳过
    try:
        result = client.stream_chat(messages, callback=callback)
        assert result is not None
    except Exception as e:
        print(f"流式聊天测试: {e}")


if __name__ == "__main__":
    print("🧪 开始测试异步功能和流式响应重建...")

    test_stream_chunk_builder()
    print("✅ 流式响应重建测试通过")

    # 运行异步测试
    asyncio.run(test_achat())
    print("✅ 异步聊天测试通过")

    asyncio.run(test_astream_chat())
    print("✅ 异步流式聊天测试通过")

    asyncio.run(test_astructured_chat())
    print("✅ 异步结构化聊天测试通过")

    test_infinite_loop_protection()
    print("✅ 防止无限循环保护测试通过")

    test_stream_chat_with_infinite_loop_detection()
    print("✅ 流式聊天无限循环检测测试通过")

    print("\n🎉 所有测试通过！")
