# Chat Mode Usage Examples

聊天模式使用示例 - 展示如何使用 NanoLLMClient 进行对话交互

## 基础聊天

```python
from core.llm_client import NanoLLMClient

# 初始化客户端
client = NanoLLMClient(model="groq/llama-3.3-70b")

# 单轮对话
response = client.chat([
    {"role": "user", "content": "你好，请介绍一下你自己"}
])
print(response)
```

## 多轮对话

```python
# 多轮对话（带历史记录）
conversation = [
    {"role": "user", "content": "什么是 Python？"},
    {"role": "assistant", "content": "Python 是一种高级编程语言..."},
    {"role": "user", "content": "Python 有哪些主要应用场景？"}
]

response = client.chat(conversation)
print(response)
```

## 获取 Token 使用统计

```python
# 获取使用统计信息
result = client.chat(
    messages=[{"role": "user", "content": "讲一个简短的故事"}],
    return_usage=True
)

print(f"内容: {result['content']}")
print(f"使用统计: {result['usage']}")
# 输出: {'input_tokens': 18, 'output_tokens': 150, 'total_tokens': 168}
```

## 流式对话

```python
# 流式输出（实时显示）
print("流式对话：")
for event in client.stream_chat([
    {"role": "user", "content": "详细解释机器学习的基本概念"}
]):
    if event["type"] == "delta":
        print(event["content"], end="", flush=True)
    elif event["type"] == "done":
        print(f"\n\n完成！使用 tokens: {event['usage']['total_tokens']}")
    elif event["type"] == "error":
        print(f"\n错误: {event['content']}")
```

## 带系统提示词的对话

```python
# 设置系统角色
messages = [
    {
        "role": "system",
        "content": "你是一个专业的 Python 编程导师，善于用简单的语言解释复杂的概念"
    },
    {
        "role": "user",
        "content": "请解释什么是装饰器（decorator）？"
    }
]

response = client.chat(messages, temperature=0.3)
print(response)
```

## 简单响应（推荐用于单轮查询）

```python
# 最简单的使用方式
answer = client.simple_response("什么是人工智能？")
print(answer)

# 带参数的简单响应
answer = client.simple_response(
    "用三句话总结量子计算",
    temperature=0.5,
    max_tokens=100
)
print(answer)
```

## 带上下文的生成

```python
# 上下文增强的生成
system_prompt = "你是一个技术文档编写助手"
user_prompt = "为以下代码添加注释"
context = """
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
"""

response = client.generate_with_context(
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    context=context
)
print(response)
```

## 对话最佳实践

1. **温度参数控制**
   - `temperature=0.1-0.3`: 确定性输出（如事实回答）
   - `temperature=0.5-0.7`: 平衡的创意和准确性
   - `temperature=0.8-1.0`: 创意性输出（如故事生成）

2. **管理对话历史**
   ```python
   # 保持对话历史的最佳方式
   conversation_history = []
   
   def chat_with_history(user_input):
       conversation_history.append({"role": "user", "content": user_input})
       response = client.chat(conversation_history)
       conversation_history.append({"role": "assistant", "content": response})
       return response
   ```

3. **错误处理**
   ```python
   try:
       response = client.chat(messages)
   except Exception as e:
       print(f"聊天失败: {e}")
       # 重试或使用备用方案
   ```

## 完整示例：交互式聊天机器人

```python
from core.llm_client import NanoLLMClient

class ChatBot:
    def __init__(self):
        self.client = NanoLLMClient()
        self.history = []
        self.system_prompt = {
            "role": "system",
            "content": "你是一个友好、专业的 AI 助手"
        }
    
    def chat(self, user_input: str) -> str:
        # 添加用户消息
        self.history.append({"role": "user", "content": user_input})
        
        # 构建完整消息列表
        messages = [self.system_prompt] + self.history
        
        # 获取响应
        response = self.client.chat(messages, temperature=0.7)
        
        # 添加助手响应
        self.history.append({"role": "assistant", "content": response})
        
        return response
    
    def clear_history(self):
        """清空对话历史"""
        self.history = []

# 使用示例
bot = ChatBot()
print("聊天机器人已启动（输入 'quit' 退出）")

while True:
    user_input = input("\n你: ")
    if user_input.lower() == 'quit':
        break
    
    response = bot.chat(user_input)
    print(f"助手: {response}")
```