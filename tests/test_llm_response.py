"""测试 LLM 对系统提示的响应"""

from core.agent import NanoAgent

agent = NanoAgent()

# 获取系统提示
system_prompt = agent._get_system_prompt()

print("🔍 系统提示分析")
print("=" * 80)
print()
print(system_prompt)
print()
print("=" * 80)
print()

# 测试一个简单的任务
print("🧪 测试 LLM 响应")
print("=" * 80)
print()

task = "读取 README.md 文件的内容"
print(f"任务: {task}")
print()

# 运行任务
result = agent.run(task, max_iterations=3)

print(f"状态: {result.get('status', 'unknown')}")
print(f"使用的工具: {result.get('tools_used', [])}")
print(f"迭代次数: {result.get('iterations', 0)}")
print()

# 检查对话历史
print("对话历史:")
print("-" * 80)
for i, msg in enumerate(agent.conversation):
    print(f"{i + 1}. {msg['role']}: {msg['content'][:200]}...")
    print()
