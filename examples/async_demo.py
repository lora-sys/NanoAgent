"""异步功能和流式响应示例"""

import asyncio
from llm.client import NanoLLMClient


async def demo_async_chat():
    """演示异步聊天"""
    print("🚀 异步聊天演示")
    client = NanoLLMClient()
    messages = [{"role": "user", "content": "你好"}]

    result = await client.achat(messages)
    print(f"异步聊天结果: {result}")


async def demo_async_streaming():
    """演示异步流式传输"""
    print("\n🌊 异步流式传输演示")
    client = NanoLLMClient()
    messages = [{"role": "user", "content": "介绍一下自己"}]

    tokens = []

    def callback(token):
        tokens.append(token)
        print(token, end="", flush=True)

    print("流式输出: ", end="", flush=True)
    result = await client.astream_chat(messages, callback=callback)
    print(f"\n\n完整响应: {result}")


def demo_stream_chunk_builder():
    """演示流式响应重建"""
    print("\n🔧 流式响应重建演示")
    client = NanoLLMClient()

    # 模拟 chunks
    chunks = []
    messages = [{"role": "user", "content": "测试"}]

    class MockChunk:
        def __init__(self, content):
            self.choices = [
                type(
                    "Choice", (), {"delta": type("Delta", (), {"content": content})()}
                )()
            ]

    chunks.append(MockChunk("你好"))
    chunks.append(MockChunk("，"))
    chunks.append(MockChunk("世界"))

    result = client.stream_chunk_builder(chunks, messages)
    print(f"重建的响应: {result}")


async def main():
    """主函数"""
    print("🎯 异步功能和流式响应演示\n")

    await demo_async_chat()
    await demo_async_streaming()
    demo_stream_chunk_builder()

    print("\n✅ 演示完成！")


if __name__ == "__main__":
    asyncio.run(main())
