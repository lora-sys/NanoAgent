"""检查对话历史"""

from core.agent import NanoAgent

agent = NanoAgent()

# 运行任务
print("运行任务...")
result = agent.run("读取 README.md 文件的内容", max_iterations=3)

print(f"\n结果状态: {result.get('status', 'unknown')}")
print(f"使用的工具: {result.get('tools_used', [])}")
print(f"迭代次数: {result.get('iterations', 0)}")

print(f"\n对话历史数量: {len(agent.conversation)}")
for i, msg in enumerate(agent.conversation):
    print(f"\n消息 {i + 1}:")
    print(f"  角色: {msg['role']}")
    print(f"  内容长度: {len(msg['content'])}")
    print(f"  内容预览: {msg['content'][:200]}")
