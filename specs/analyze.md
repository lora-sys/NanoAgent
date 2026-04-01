# Analyze Mode Usage Examples

分析模式使用示例 - 展示如何使用 NanoLLMClient 进行各种分析任务

## 代码分析

```python
from core.llm_client import NanoLLMClient

client = NanoLLMClient(model="groq/llama-3.3-70b")

# 代码质量分析
code = """
def process_data(data):
    result = []
    for item in data:
        if item['value'] > 0:
            result.append(item['value'] * 2)
    return result
"""

messages = [
    {
        "role": "system",
        "content": "你是一位资深的代码审查专家，擅长识别代码问题和改进机会"
    },
    {
        "role": "user",
        "content": f"""请分析以下代码的质量：

{code}

分析维度：
1. 代码风格
2. 性能问题
3. 错误处理
4. 可读性
5. 改进建议

请以 JSON 格式返回分析结果"""
    }
]

analysis = client.chat(messages, temperature=0.2)
print(analysis)
```

## 文本情感分析

```python
# 情感分析
texts = [
    "这个产品太棒了，我非常喜欢！",
    "服务态度很差，不会再来了",
    "一般般，没什么特别的"
]

for text in texts:
    sentiment = client.simple_response(
        f"""分析以下文本的情感倾向（正面/负面/中性），并给出置信度（0-1）：

文本：{text}

返回格式：{{"sentiment": "...", "confidence": 0.XX, "reasoning": "..."}}""",
        temperature=0.1
    )
    print(f"文本: {text}")
    print(f"情感: {sentiment}\n")
```

## 数据分析（使用结构化输出）

```python
from pydantic import BaseModel
from typing import List

class DataInsight(BaseModel):
    """数据洞察"""
    trend: str
    key_findings: List[str]
    recommendations: List[str]
    confidence: float

# 分析销售数据
sales_data = """
Q1: 销售额 100万，环比增长 15%
Q2: 销售额 120万，环比增长 20%
Q3: 销售额 90万，环比下降 25%
Q4: 销售额 130万，环比增长 44%
"""

messages = [
    {
        "role": "system",
        "content": "你是一位数据分析师，擅长从数据中提取洞察"
    },
    {
        "role": "user",
        "content": f"""分析以下销售数据并提供洞察：

{sales_data}

请识别趋势、关键发现和建议"""
    }
]

insights = client.structured_chat(messages, DataInsight)

print(f"趋势: {insights.trend}")
print(f"\n关键发现:")
for finding in insights.key_findings:
    print(f"  - {finding}")
print(f"\n建议:")
for rec in insights.recommendations:
    print(f"  - {rec}")
print(f"\n置信度: {insights.confidence}")
```

## 文档分析

```python
# 文档内容分析
document = """
人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。
这些任务包括学习、推理、问题解决、理解语言和感知。
"""

messages = [
    {
        "role": "system",
        "content": "你是一位专业的内容分析师"
    },
    {
        "role": "user",
        "content": f"""分析以下文档：

{document}

分析内容：
1. 文档类型
2. 主要主题
3. 关键词提取
4. 摘要生成（50 字）
5. 难度级别

请以结构化格式返回"""
    }
]

doc_analysis = client.chat(messages, temperature=0.3)
print(doc_analysis)
```

## 错误日志分析

```python
# 日志分析
error_logs = """
[ERROR] 2025-01-15 10:23:45 - Connection timeout to database server
[ERROR] 2025-01-15 10:24:12 - Failed to authenticate user
[ERROR] 2025-01-15 10:25:30 - Connection timeout to database server
[ERROR] 2025-01-15 10:26:45 - Out of memory exception
"""

messages = [
    {
        "role": "system",
        "content": "你是一位 DevOps 工程师，擅长分析系统日志和故障排查"
    },
    {
        "role": "user",
        "content": f"""分析以下错误日志：

{error_logs}

请提供：
1. 错误模式识别
2. 根本原因分析
3. 优先级排序
4. 修复建议"""
    }
]

log_analysis = client.chat(messages, temperature=0.2)
print(log_analysis)
```

## 竞品分析

```python
# 竞品分析
competitor_info = """
产品 A: 价格 $99，功能全面，用户体验好，更新频繁
产品 B: 价格 $49，功能基础，用户体验一般，更新较少
产品 C: 价格 $149，功能强大，用户体验优秀，专业版
"""

messages = [
    {
        "role": "system",
        "content": "你是一位市场分析师，擅长竞品分析"
    },
    {
        "role": "user",
        "content": f"""分析以下竞品信息：

{competitor_info}

分析维度：
1. 市场定位
2. 价格策略
3. 功能对比
4. 优劣势分析
5. 市场机会

请以表格形式呈现对比结果"""
    }
]

competitor_analysis = client.chat(messages, temperature=0.3)
print(competitor_analysis)
```

## 用户反馈分析

```python
# 用户反馈分析
feedback_list = [
    "界面很漂亮，但是功能不够完善",
    "加载速度太慢了",
    "客服响应很快，解决了我的问题",
    "价格有点贵，希望能有折扣",
    "新版本很好用，推荐给大家"
]

feedback_text = "\n".join([f"{i+1}. {f}" for i, f in enumerate(feedback_list)])

messages = [
    {
        "role": "system",
        "content": "你是一位产品经理，擅长分析用户反馈"
    },
    {
        "role": "user",
        "content": f"""分析以下用户反馈：

{feedback_text}

分析要求：
1. 分类反馈（正面/负面/中性）
2. 提取关键问题
3. 优先级排序
4. 改进建议"""
    }
]

feedback_analysis = client.chat(messages, temperature=0.2)
print(feedback_analysis)
```

## 风险评估

```python
# 项目风险评估
project_info = """
项目：新电商系统开发
预算：500万
时间：6个月
团队：10人
技术栈：微服务架构，云原生
"""

messages = [
    {
        "role": "system",
        "content": "你是一位项目风险管理专家"
    },
    {
        "role": "user",
        "content": f"""对以下项目进行风险评估：

{project_info}

请识别：
1. 技术风险
2. 进度风险
3. 成本风险
4. 人员风险
5. 缓解策略

按风险等级（高/中/低）分类"""
    }
]

risk_assessment = client.chat(messages, temperature=0.3)
print(risk_assessment)
```

## 性能分析

```python
# 系统性能分析
performance_data = """
API 响应时间：
- 平均: 250ms
- P95: 800ms
- P99: 1500ms

错误率：
- 4xx: 2%
- 5xx: 0.5%

并发用户：
- 峰值: 5000
- 平均: 2000
"""

messages = [
    {
        "role": "system",
        "content": "你是一位性能优化专家"
    },
    {
        "role": "user",
        "content": f"""分析以下系统性能数据：

{performance_data}

请评估：
1. 性能瓶颈
2. SLA 合规性
3. 优化建议
4. 容量规划建议"""
    }
]

performance_analysis = client.chat(messages, temperature=0.2)
print(performance_analysis)
```

## 文本相似度分析

```python
# 文本相似度分析
text1 = "人工智能将改变未来的工作方式"
text2 = "AI 将彻底改变我们未来的工作模式"
text3 = "今天的天气很好，适合外出散步"

messages = [
    {
        "role": "system",
        "content": "你是一位 NLP 专家，擅长文本相似度分析"
    },
    {
        "role": "user",
        "content": f"""分析以下文本对的相似度：

文本 1: {text1}
文本 2: {text2}
文本 3: {text3}

请比较：
1. 文本 1 vs 文本 2 的相似度
2. 文本 1 vs 文本 3 的相似度
3. 文本 2 vs 文本 3 的相似度

返回格式：{{"similarity_scores": [0-1], "reasoning": "..."}}"""
    }
]

similarity_analysis = client.chat(messages, temperature=0.1)
print(similarity_analysis)
```

## 完整示例：自动化分析系统

```python
from core.llm_client import NanoLLMClient
from pydantic import BaseModel
from typing import List, Optional
import json

class AnalysisResult(BaseModel):
    """分析结果"""
    category: str
    severity: str
    findings: List[str]
    recommendations: List[str]
    confidence: float

class AutoAnalyzer:
    def __init__(self):
        self.client = NanoLLMClient()
    
    def analyze_code(self, code: str) -> AnalysisResult:
        """代码分析"""
        messages = [
            {
                "role": "system",
                "content": "你是一位代码审查专家"
            },
            {
                "role": "user",
                "content": f"""审查以下代码并返回结构化分析：

{code}

返回 JSON 格式，包含：
- category: 问题类型
- severity: 严重程度（critical/high/medium/low）
- findings: 发现的问题列表
- recommendations: 改进建议
- confidence: 置信度"""
            }
        ]
        return self.client.structured_chat(messages, AnalysisResult)
    
    def analyze_text(self, text: str, analysis_type: str) -> str:
        """文本分析"""
        prompts = {
            "sentiment": "分析文本的情感倾向",
            "summary": "生成文本摘要",
            "keywords": "提取关键词",
            "readability": "评估可读性"
        }
        
        messages = [
            {
                "role": "system",
                "content": f"你是一位{prompts.get(analysis_type, '文本')}分析师"
            },
            {
                "role": "user",
                "content": f"分析以下文本：\n{text}"
            }
        ]
        return self.client.chat(messages, temperature=0.3)
    
    def batch_analyze(self, items: List[str], analysis_type: str) -> List[dict]:
        """批量分析"""
        results = []
        for i, item in enumerate(items):
            print(f"分析第 {i+1}/{len(items)} 项...")
            
            if analysis_type == "code":
                result = self.analyze_code(item)
                results.append(result.model_dump())
            else:
                result = self.analyze_text(item, analysis_type)
                results.append({"index": i, "result": result})
        
        return results
    
    def generate_report(self, analyses: List[dict]) -> str:
        """生成分析报告"""
        messages = [
            {
                "role": "system",
                "content": "你是一位专业报告撰写专家"
            },
            {
                "role": "user",
                "content": f"""根据以下分析结果生成一份综合报告：

{json.dumps(analyses, indent=2, ensure_ascii=False)}

报告要求：
1. 执行摘要
2. 关键发现
3. 详细分析
4. 建议
5. 结论"""
            }
        ]
        return self.client.chat(messages, temperature=0.4)

# 使用示例
analyzer = AutoAnalyzer()

# 代码分析示例
code_samples = [
    "def quicksort(arr): return arr if len(arr) <= 1 else quicksort([x for x in arr[1:] if x < arr[0]]) + [arr[0]] + quicksort([x for x in arr[1:] if x >= arr[0]])",
    "for i in range(len(items)): if items[i] > 0: results.append(items[i])"
]

code_analyses = analyzer.batch_analyze(code_samples, "code")
print("代码分析结果:")
print(json.dumps(code_analyses, indent=2, ensure_ascii=False))

# 文本分析示例
texts = [
    "这个产品非常棒，我强烈推荐！",
    "质量太差了，浪费钱",
    "还可以，符合预期"
]

text_analyses = analyzer.batch_analyze(texts, "sentiment")
print("\n文本分析结果:")
print(json.dumps(text_analyses, indent=2, ensure_ascii=False))

# 生成综合报告
report = analyzer.generate_report(code_analyses + text_analyses)
print("\n综合分析报告:")
print(report)
```