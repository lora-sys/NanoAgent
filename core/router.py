"""
混合路由系统 - NanoAgent
结合规则路由和 LLM 路由，实现高效且灵活的任务分类
"""

import json
import os
from typing import Dict, List, Optional
from spec.models import TaskType, RoutingDecision


class RuleBasedRouter:
    """基于规则的路由器 - 第一层，快速确定路由"""

    def __init__(self, rules_file: str = None):
        self.rules = self._load_rules(rules_file)

    def _load_rules(self, rules_file: str = None) -> Dict[str, Dict]:
        """加载路由规则"""
        if rules_file and os.path.exists(rules_file):
            with open(rules_file, "r", encoding="utf-8") as f:
                return json.load(f)

        # 默认规则
        return {
            "code": {
                "keywords": [
                    "开发",
                    "实现",
                    "构建",
                    "编写",
                    "create",
                    "implement",
                    "build",
                    "develop",
                    "代码",
                    "api",
                    "接口",
                    "function",
                    "函数",
                    "class",
                    "类",
                ],
                "patterns": ["开发.*", "实现.*", "build.*", "implement.*"],
                "tech_keywords": [
                    "python",
                    "javascript",
                    "react",
                    "vue",
                    "fastapi",
                    "flask",
                    "django",
                    "数据库",
                    "database",
                ],
                "confidence": 0.95,
            },
            "writing": {
                "keywords": [
                    "写",
                    "撰写",
                    "文章",
                    "博客",
                    "文档",
                    "报告",
                    "write",
                    "article",
                    "blog",
                    "document",
                    "report",
                    "论文",
                    "paper",
                ],
                "patterns": ["写.*", "撰写.*", "write.*", "draft.*"],
                "style_keywords": [
                    "正式",
                    "学术",
                    "博客",
                    "幽默",
                    "professional",
                    "academic",
                    "blog",
                ],
                "confidence": 0.90,
            },
            "analyze": {
                "keywords": [
                    "分析",
                    "评估",
                    "研究",
                    "调查",
                    "review",
                    "analysis",
                    "evaluate",
                    "study",
                    "investigate",
                    "调查报告",
                    "评估报告",
                ],
                "patterns": ["分析.*", "评估.*", "review.*", "analyze.*"],
                "analysis_types": [
                    "性能",
                    "安全",
                    "代码",
                    "数据",
                    "performance",
                    "security",
                    "code",
                    "data",
                ],
                "confidence": 0.92,
            },
            "chat": {
                "keywords": [
                    "聊天",
                    "对话",
                    "讨论",
                    "咨询",
                    "chat",
                    "conversation",
                    "discuss",
                    "ask",
                    "question",
                ],
                "patterns": ["聊聊", "谈谈", "讨论", "帮我看看"],
                "confidence": 0.85,
            },
        }

    def route(self, user_input: str) -> Optional[RoutingDecision]:
        """基于规则进行路由"""
        user_input_lower = user_input.lower()

        best_match = None
        best_score = 0

        for task_type, rules in self.rules.items():
            score = self._calculate_match_score(user_input_lower, rules)
            if score > best_score:
                best_score = score
                best_match = task_type

        if best_score > 0.3:  # 阈值，低于此值认为匹配不足
            confidence = min(best_score * self.rules[best_match]["confidence"], 1.0)
            return RoutingDecision(
                task_type=TaskType(best_match),
                confidence=confidence,
                template_modules=self._get_template_modules(best_match),
                reasoning=f"规则路由匹配：检测到关键词和模式，置信度 {confidence:.2f}",
            )

        return None

    def _calculate_match_score(self, user_input: str, rules: Dict) -> float:
        """计算匹配分数"""
        import re

        score = 0

        # 关键词匹配
        keywords = rules.get("keywords", [])
        for keyword in keywords:
            if keyword.lower() in user_input:
                score += 0.3

        # 技术关键词匹配
        tech_keywords = rules.get("tech_keywords", [])
        for tech_keyword in tech_keywords:
            if tech_keyword.lower() in user_input:
                score += 0.2

        # 风格关键词匹配
        style_keywords = rules.get("style_keywords", [])
        for style_keyword in style_keywords:
            if style_keyword.lower() in user_input:
                score += 0.15

        # 分析类型匹配
        analysis_types = rules.get("analysis_types", [])
        for analysis_type in analysis_types:
            if analysis_type.lower() in user_input:
                score += 0.2

        # 模式匹配（正则表达式）
        patterns = rules.get("patterns", [])
        for pattern in patterns:
            try:
                if re.search(pattern, user_input, re.IGNORECASE):
                    score += 0.3
            except re.error:
                # 如果正则表达式无效，跳过该模式
                continue

        # 归一化分数到 0-1
        return min(score, 1.0)

    def _get_template_modules(self, task_type: str) -> List[str]:
        """获取模板模块列表"""
        module_map = {
            "code": ["base_spec", "code_logic", "code_api", "project_plan"],
            "writing": ["base_spec", "writing_style", "writing_structure"],
            "analyze": ["base_spec", "analyze_framework", "analyze_report"],
            "chat": ["base_spec", "chat_protocol"],
        }
        return module_map.get(task_type, ["base_spec"])


class LLMRouter:
    """基于 LLM 的路由器 - 第二层，处理复杂或模糊的请求"""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def route(self, user_input: str) -> RoutingDecision:
        """使用 LLM 进行路由决策"""
        prompt = f"""你是一个任务分类专家。请分析以下用户请求，并确定任务类型。

用户请求：
{user_input}

任务类型：
- code: 编程开发任务（实现功能、编写代码、构建系统等）
- writing: 写作任务（撰写文章、文档、报告、博客等）
- analyze: 分析任务（代码分析、数据分析、性能评估等）
- chat: 对话任务（聊天、咨询、讨论等）

请以 JSON 格式返回，包含以下字段：
{{
  "task_type": "任务类型（code/writing/analyze/chat）",
  "confidence": 0.0-1.0 之间的置信度,
  "reasoning": "详细的推理过程"
}}"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}], temperature=0.3
            )

            # 解析 LLM 响应
            import re

            json_match = re.search(r"\{[^}]+\}", response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())

                return RoutingDecision(
                    task_type=TaskType(result["task_type"]),
                    confidence=result["confidence"],
                    template_modules=self._get_template_modules(result["task_type"]),
                    reasoning=f"LLM 路由决策：{result['reasoning']}",
                )
        except Exception as e:
            print(f"LLM 路由失败: {e}")

        # 回退到默认
        return RoutingDecision(
            task_type=TaskType.CHAT,
            confidence=0.5,
            template_modules=["base_spec"],
            reasoning="LLM 路由失败，回退到默认类型",
        )

    def _get_template_modules(self, task_type: str) -> List[str]:
        """获取模板模块列表"""
        module_map = {
            "code": ["base_spec", "code_logic", "code_api", "project_plan"],
            "writing": ["base_spec", "writing_style", "writing_structure"],
            "analyze": ["base_spec", "analyze_framework", "analyze_report"],
            "chat": ["base_spec", "chat_protocol"],
        }
        return module_map.get(task_type, ["base_spec"])


class HybridRouter:
    """混合路由器 - 结合规则路由和 LLM 路由"""

    def __init__(self, llm_client, rules_file: str = None):
        self.rule_router = RuleBasedRouter(rules_file)
        self.llm_router = LLMRouter(llm_client)

    def route(self, user_input: str) -> RoutingDecision:
        """
        混合路由决策：
        1. 首先尝试规则路由（快速、确定）
        2. 如果规则路由置信度 > 0.7，直接返回
        3. 否则使用 LLM 路由进行更精细的分析
        """
        # 第一层：规则路由
        rule_decision = self.rule_router.route(user_input)

        if rule_decision and rule_decision.confidence > 0.7:
            print(
                f"✓ 规则路由匹配: {rule_decision.task_type} (置信度: {rule_decision.confidence:.2f})"
            )
            return rule_decision

        # 第二层：LLM 路由
        print("⚡ 使用 LLM 路由进行精细分析...")
        llm_decision = self.llm_router.route(user_input)

        return llm_decision

    def explain_routing(self, user_input: str, decision: RoutingDecision) -> str:
        """解释路由决策"""
        explanation = f"""
路由决策报告
============

用户输入: {user_input}

决策结果:
- 任务类型: {decision.task_type.value}
- 置信度: {decision.confidence:.2%}
- 推理: {decision.reasoning}
- 模板模块: {", ".join(decision.template_modules)}

路由路径:
{"规则路由 (快速匹配)" if decision.confidence > 0.7 else "LLM 路由 (语义分析)"}
"""
        return explanation
