"""测试完整对话历史"""

from core.agent import NanoAgent

agent = NanoAgent()

# 运行任务
result = agent.run("读取 README.md 文件的内容", max_iterations=3)

print("完整对话历史:")
print("=" * 80)
print()

for i, msg in enumerate(agent.conversation):
    print(f"消息 {i + 1}:")
    print(f"  角色: {msg['role']}")
    print(f"  内容: {msg['content']}")
    print()
    print("-" * 80)
    print()
