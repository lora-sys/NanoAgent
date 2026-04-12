"""
Planning 阶段处理器

负责生成执行计划
"""

from loguru import logger
import json

from .base import BasePhase
from core.prompt import SYSTEM_PROMPT, PLANNING_PROMPT
from domain.models.models import AgentPlan, PlanStep


class PlanningPhase(BasePhase):
    """Planning 阶段处理器"""

    def execute(
        self,
        task: str,
        spec_content: str,
        current_context: str = "",
    ) -> AgentPlan:
        """
        执行 Planning 阶段

        Args:
            task: 任务描述
            spec_content: Spec 内容
            current_context: 当前上下文

        Returns:
            执行计划
        """
        logger.info("=== Planning Phase ===")

        prompt = PLANNING_PROMPT.format(
            task_description=task,
            task_spec=spec_content,
            current_context=current_context,
            available_tools=self.tool_registry.get_tool_descriptions()
            if self.tool_registry
            else "No tools available",
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": prompt,
            },
        ]

        try:
            # 尝试使用结构化输出
            plan = self.llm_client.structured_chat(messages, AgentPlan, temperature=0.5)
            logger.info(f"Plan generated with {len(plan.steps)} steps")
            return plan

        except Exception as e:
            logger.warning(
                f"Structured planning failed, falling back to JSON parsing: {e}"
            )
            return self._fallback_planning(messages)

    def _fallback_planning(self, messages: list) -> AgentPlan:
        """回退规划：使用普通 JSON 解析"""
        try:
            response = self.llm_client.chat(messages, temperature=0.5)
            plan_data = json.loads(response)

            plan = AgentPlan(
                steps=[
                    PlanStep(
                        step_id=step["step_id"],
                        goal=step["goal"],
                        suggested_tools=step.get("tool", "").split(","),
                    )
                    for step in plan_data.get("steps", [])
                ],
                overall_goal=plan_data.get("overview", ""),
            )
            logger.info(f"Plan generated with {len(plan.steps)} steps (fallback)")
            return plan

        except Exception as e2:
            logger.error(f"Planning error: {e2}")
            return AgentPlan(
                steps=[PlanStep(step_id=1, goal="Execute task", suggested_tools=[])],
                overall_goal="Fallback plan",
            )
