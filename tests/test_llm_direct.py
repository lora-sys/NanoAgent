"""直接测试 LLM 客户端"""

from llm.client import NanoLLMClient

client = NanoLLMClient()

messages = [
    {"role": "system", "content": "你是一个助手，帮助用户完成任务。"},
    {"role": "user", "content": "你好"},
]

print("测试 LLM 客户端...")
print("=" * 80)
print()

try:
    response = client.chat(messages)
    print("✅ LLM 响应成功:")
    print(f"   响应: {response}")
except Exception as e:
    print(f"❌ LLM 响应失败: {e}")
    import traceback

    traceback.print_exc()
