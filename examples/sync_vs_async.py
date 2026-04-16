"""同步 vs 异步聊天对比演示"""

import asyncio
import time
from llm.client import NanoLLMClient


def demo_sync_chat():
    """演示同步聊天"""
    print("🔄 同步聊天演示")
    client = NanoLLMClient()
    messages = [{"role": "user", "content": "你好"}]

    start = time.time()
    result = client.chat(messages)
    end = time.time()

    print(f"结果: {result}")
    print(f"耗时: {(end - start) * 1000:.2f}ms")
    return end - start


async def demo_async_chat():
    """演示异步聊天"""
    print("\n⚡ 异步聊天演示")
    client = NanoLLMClient()
    messages = [{"role": "user", "content": "你好"}]

    start = time.time()
    result = await client.achat(messages)
    end = time.time()

    print(f"结果: {result}")
    print(f"耗时: {(end - start) * 1000:.2f}ms")
    return end - start


def demo_multiple_sync_requests():
    """演示多个同步请求"""
    print("\n🔄 多个同步请求演示")
    client = NanoLLMClient()
    messages_list = [
        [{"role": "user", "content": "你好"}],
        [{"role": "user", "content": "介绍一下自己"}],
        [{"role": "user", "content": "天气怎么样"}],
    ]

    start = time.time()
    results = []
    for messages in messages_list:
        result = client.chat(messages)
        results.append(result)
    end = time.time()

    print(f"完成 {len(results)} 个请求")
    print(f"总耗时: {(end - start) * 1000:.2f}ms")
    print(f"平均耗时: {(end - start) * 1000 / len(results):.2f}ms")
    return end - start


async def demo_multiple_async_requests():
    """演示多个异步请求（并发）"""
    print("\n⚡ 多个异步请求（并发）演示")
    client = NanoLLMClient()
    messages_list = [
        [{"role": "user", "content": "你好"}],
        [{"role": "user", "content": "介绍一下自己"}],
        [{"role": "user", "content": "天气怎么样"}],
    ]

    start = time.time()
    tasks = [client.achat(messages) for messages in messages_list]
    results = await asyncio.gather(*tasks)
    end = time.time()

    print(f"完成 {len(results)} 个并发请求")
    print(f"总耗时: {(end - start) * 1000:.2f}ms")
    print(f"平均耗时: {(end - start) * 1000 / len(results):.2f}ms")
    return end - start


async def main():
    """主函数"""
    print("🎯 同步 vs 异步聊天对比演示\n")

    # 单个请求对比
    sync_time = demo_sync_chat()
    async_time = await demo_async_chat()

    print(f"\n📊 单个请求对比:")
    print(f"同步: {sync_time * 1000:.2f}ms")
    print(f"异步: {async_time * 1000:.2f}ms")
    print(f"差异: {abs(sync_time - async_time) * 1000:.2f}ms")

    # 多个请求对比
    print("\n" + "=" * 50)
    sync_multi_time = demo_multiple_sync_requests()
    async_multi_time = await demo_multiple_async_requests()

    print(f"\n📊 多个请求对比:")
    print(f"同步（串行）: {sync_multi_time * 1000:.2f}ms")
    print(f"异步（并发）: {async_multi_time * 1000:.2f}ms")
    print(f"性能提升: {(sync_multi_time / async_multi_time):.2f}x")
    print(f"时间节省: {(sync_multi_time - async_multi_time) * 1000:.2f}ms")

    print("\n✅ 演示完成！")


if __name__ == "__main__":
    asyncio.run(main())