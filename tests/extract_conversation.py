"""提取对话历史"""

from core.agent import NanoAgent
import json

agent = NanoAgent()

# 运行任务
result = agent.run("读取 README.md 文件的内容", max_iterations=3)

# 保存对话历史到文件
with open("/tmp/conversation.json", "w") as f:
    json.dump(agent.conversation, f, indent=2, ensure_ascii=False)

print("对话历史已保存到 /tmp/conversation.json")
print(f"消息数量: {len(agent.conversation)}")

for i, msg in enumerate(agent.conversation):
    print(f"{i + 1}. {msg['role']}: {msg['content'][:100]}...")
