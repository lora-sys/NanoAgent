# Writing Mode Usage Examples

写作模式使用示例 - 展示如何使用 NanoLLMClient 进行各种写作任务

## 文章写作

```python
from core.llm_client import NanoLLMClient

client = NanoLLMClient(model="groq/llama-3.3-70b")

# 写一篇文章
messages = [
    {
        "role": "system",
        "content": "你是一位专业的技术作家，擅长撰写清晰、有深度的技术文章"
    },
    {
        "role": "user",
        "content": "写一篇关于 '为什么选择 Python 作为第一门编程语言' 的文章，约 800 字"
    }
]

article = client.chat(messages, temperature=0.7, max_tokens=1000)
print(article)
```

## 流式写作（实时生成）

```python
# 流式生成文章（实时看到生成过程）
print("开始生成文章...\n")

for event in client.stream_chat([
    {
        "role": "system",
        "content": "你是一位优秀的科幻小说作家"
    },
    {
        "role": "user",
        "content": "写一个关于 AI 觉醒的短篇故事开头"
    }
]):
    if event["type"] == "delta":
        print(event["content"], end="", flush=True)

print("\n\n文章生成完成！")
```

## 博客文章写作

```python
# 生成结构化的博客文章
blog_outline = """
# 标题: 2025 年 AI 发展趋势预测

## 引言
- AI 的快速发展
- 本文目的

## 主要趋势
1. 大模型的普及
2. AI 在医疗领域的应用
3. 自动驾驶的突破

## 结论
- 对未来的展望
"""

messages = [
    {
        "role": "system",
        "content": "你是一位专业的博客作者，擅长撰写 engaging 的技术博客"
    },
    {
        "role": "user",
        "content": f"根据以下大纲写一篇完整的博客文章：\n{blog_outline}"
    }
]

blog_post = client.chat(messages, temperature=0.6)
print(blog_post)
```

## 文档生成（使用结构化输出）

```python
from pydantic import BaseModel
from typing import List

class DocumentStructure(BaseModel):
    """文档结构"""
    title: str
    sections: List[dict]
    summary: str
    word_count: int

# 生成文档结构
messages = [
    {
        "role": "system",
        "content": "你是一个技术文档规划专家"
    },
    {
        "role": "user",
        "content": "为一个 '如何使用 Docker' 的教程规划文档结构"
    }
]

doc_structure = client.structured_chat(messages, DocumentStructure)

print(f"标题: {doc_structure.title}")
print(f"摘要: {doc_structure.summary}")
print(f"预计字数: {doc_structure.word_count}")
print("\n章节:")
for section in doc_structure.sections:
    print(f"  - {section}")
```

## 创意写作

```python
# 创意故事生成
creative_prompt = """
写一个微型科幻故事（300 字以内）：
- 设定：2050 年的月球基地
- 主角：一位孤独的月球工程师
- 冲突：发现了一个无法解释的信号
- 结局：开放式
"""

story = client.simple_response(creative_prompt, temperature=0.9)
print(story)
```

## 内容优化和改写

```python
# 内容优化
original_text = """
AI 正在改变我们的生活方式。它可以帮助我们做很多事情。比如写代码、画画、写文章。
AI 的发展很快。未来 AI 会更强大。
"""

rewrite_prompt = f"""
请将以下文本改写为更专业、更流畅的版本，保持原意但提升表达质量：

{original_text}

要求：
- 使用更丰富的词汇
- 改善句子结构
- 保持专业性
- 约 100 字
"""

improved_text = client.simple_response(rewrite_prompt, temperature=0.3)
print(improved_text)
```

## 技术文档编写

```python
# 生成 API 文档
api_spec = """
函数名: calculate fibonacci
输入: n (正整数)
输出: 第 n 个斐波那契数
"""

messages = [
    {
        "role": "system",
        "content": "你是一位技术文档编写专家，遵循清晰的文档标准"
    },
    {
        "role": "user",
        "content": f"根据以下函数规范编写完整的 API 文档（包括描述、参数、返回值、示例、边界情况）：\n{api_spec}"
    }
]

api_doc = client.chat(messages, temperature=0.2)
print(api_doc)
```

## 邮件写作

```python
# 专业邮件生成
email_context = {
    "recipient": "张经理",
    "subject": "项目进度汇报",
    "key_points": [
        "项目已完成 80%",
        "预计下周完成",
        "需要确认一些细节"
    ],
    "tone": "professional"
}

email_prompt = f"""
写一封给 {email_context['recipient']} 的专业邮件：

主题：{email_context['subject']}

需要包含的内容：
{chr(10).join(f"- {point}" for point in email_context['key_points'])}

语气：{email_context['tone']}
要求：简洁、清晰、专业
"""

email = client.simple_response(email_prompt, temperature=0.3)
print(email)
```

## 创意文案写作

```python
# 产品营销文案
product_info = """
产品：智能咖啡机
特点：语音控制、自动研磨、可调节浓度
目标用户：忙碌的上班族
"""

messages = [
    {
        "role": "system",
        "content": "你是一位创意文案专家，擅长撰写吸引人的产品文案"
    },
    {
        "role": "user",
        "content": f"为以下产品撰写 3 条不同风格的营销文案（每条 50 字以内）：\n{product_info}"
    }
]

copywritings = client.chat(messages, temperature=0.8)
print(copywritings)
```

## 多版本生成（A/B 测试）

```python
# 生成多个版本供选择
base_content = "我们的新产品将在下个月发布，它将彻底改变您的工作方式"

versions = []
for i in range(3):
    version = client.simple_response(
        f"为以下内容创作一个更有吸引力的版本（版本 {i+1}）：\n{base_content}",
        temperature=0.7
    )
    versions.append(version)
    print(f"\n版本 {i+1}:")
    print(version)
```

## 写作质量检查

```python
# 内容质量评估
text_to_check = """
这里是一段需要检查的文本内容...
"""

messages = [
    {
        "role": "system",
        "content": "你是一位专业的内容编辑，擅长评估写作质量"
    },
    {
        "role": "user",
        "content": f"""请评估以下文本的质量，并给出改进建议：

文本：
{text_to_check}

评估维度：
1. 清晰度
2. 准确性
3. 流畅性
4. 专业性
5. 改进建议

请以 JSON 格式返回评估结果"""
    }
]

evaluation = client.chat(messages, temperature=0.3)
print(evaluation)
```

## 完整示例：自动化文章生成器

```python
from core.llm_client import NanoLLMClient
from pydantic import BaseModel
from typing import List

class ArticleOutline(BaseModel):
    """文章大纲"""
    title: str
    sections: List[dict]
    estimated_words: int

class ArticleGenerator:
    def __init__(self):
        self.client = NanoLLMClient()
    
    def generate_outline(self, topic: str) -> ArticleOutline:
        """生成文章大纲"""
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的文章规划师"
            },
            {
                "role": "user",
                "content": f"为 '{topic}' 生成一个详细的文章大纲"
            }
        ]
        return self.client.structured_chat(messages, ArticleOutline)
    
    def write_section(self, section_title: str, section_content_hint: str) -> str:
        """写一个章节"""
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的文章写作者"
            },
            {
                "role": "user",
                "content": f"""写一个章节：

标题：{section_title}
内容提示：{section_content_hint}
要求：约 300 字，内容丰富，逻辑清晰"""
            }
        ]
        return self.client.chat(messages, temperature=0.6)
    
    def generate_article(self, topic: str) -> str:
        """生成完整文章"""
        # 1. 生成大纲
        outline = self.generate_outline(topic)
        print(f"生成大纲: {outline.title}")
        
        # 2. 逐节写作
        full_article = f"# {outline.title}\n\n"
        
        for section in outline.sections:
            print(f"正在写: {section.get('title', '未命名章节')}")
            section_text = self.write_section(
                section.get('title', ''),
                section.get('description', '')
            )
            full_article += f"## {section.get('title', '')}\n\n{section_text}\n\n"
        
        return full_article

# 使用示例
generator = ArticleGenerator()
article = generator.generate_article("人工智能在教育领域的应用")
print(article)
```