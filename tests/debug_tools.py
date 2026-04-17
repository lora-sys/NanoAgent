"""调试工具注册问题"""

from core.agent import NanoAgent

agent = NanoAgent()

# 获取工具列表
tool_list = agent.tools.get_tool_list()

print("🔍 工具注册调试")
print("=" * 80)
print()

for tool in tool_list:
    print(f"工具名: {tool['function']['name']}")
    print(f"描述: {tool['function']['description']}")
    print(f"参数: {tool['function']['parameters']}")
    print()
    print("-" * 80)
    print()

# 检查工具执行
print("🧪 测试工具执行")
print("=" * 80)
print()

try:
    result = agent.tools.execute("read_file", {"path": "README.md"})
    print("✅ read_file 执行成功:")
    print(f"   结果: {result}")
except Exception as e:
    print(f"❌ read_file 执行失败: {e}")

print()

try:
    result = agent.tools.execute("list_files", {"path": "."})
    print("✅ list_files 执行成功:")
    print(f"   结果: {result}")
except Exception as e:
    print(f"❌ list_files 执行失败: {e}")
