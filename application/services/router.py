"""
混合路由系统 - NanoAgent

使用 LLM 进行任务分类，快速确定路由
"""

import json
from loguru import logger
from domain.models.models import TaskType, RoutingDecision

# 模板模块映射
TEMPLATE_MODULE_MAP = {
    "code": ["base_spec", "code_logic", "code_api", "project_plan"],
    "writing": ["base_spec", "writing_style", "writing_structure"],
    "analyze": ["base_spec", "analyze_framework", "analyze_report"],
    "chat": ["base_spec", "chat_protocol"],
}


def get_template_modules_for_task(task_type: str) -> list[str]:
    """根据任务类型获取模板模块列表"""
    return TEMPLATE_MODULE_MAP.get(task_type, ["base_spec"])


class HybridRouter:
    """混合路由器 - 使用 LLM 进行分类"""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def route(self, user_input: str) -> RoutingDecision:
        """使用 LLM 进行路由决策"""
        prompt = f"""分析用户请求，确定任务类型。只返回 JSON。

请求: {user_input}

类型:
- code: 编程、开发、实现、构建
- writing: 文章、报告、文档
- analyze: 数据分析、研究、评估
- chat: 对话、问答、咨询

返回 JSON: {{"task_type": "code/writing/analyze/chat", "confidence": 0.0-1.0, "reasoning": "简要说明为什么"}}"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}], temperature=0.3,
            )
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(response[start:end])
                task_type = result.get("task_type", "chat")
                try:
                    task_enum = TaskType(task_type)
                except ValueError:
                    task_enum = TaskType.CHAT

                return RoutingDecision(
                    task_type=task_enum,
                    confidence=float(result.get("confidence", 0.5)),
                    template_modules=get_template_modules_for_task(task_type),
                    reasoning=result.get("reasoning", "LLM 路由决策"),
                )
        except Exception as e:
            logger.warning(f"LLM 路由失败: {e}")

        return RoutingDecision(
            task_type=TaskType.CHAT,
            confidence=0.5,
            template_modules=["base_spec"],
            reasoning="路由失败，回退到默认类型",
        )
