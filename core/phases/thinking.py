"""
Think 阶段处理器

负责分析当前状态并决定下一步行动
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from loguru import logger

from .base import BasePhase
from core.prompt import REACT_THINK_PROMPT


class ThinkAction(BaseModel):
    """思考结果"""

    action: str = Field(
        ..., description="动作: tool_call, complete, wait, stage_complete, continue"
    )
    tool: Optional[str] = Field(default=None, description="工具名称")
    arguments: Optional[Dict[str, Any]] = Field(default_factory=dict)
    reason: Optional[str] = Field(default=None, description="原因说明")


class ThinkingPhase(BasePhase):
    """Think 阶段处理器"""

    def execute(
        self,
        task: str,
        context: Dict,
        observations: list,
        step_count: int = 0,
        spec: Any = None,
        state: Any = None,
    ) -> Dict[str, Any]:
        """执行 Think 阶段"""
        logger.info(f"=== Think Phase (Step {step_count + 1}) ===")

        context = context or {}
        prompt = self._build_prompt(task, context, observations, step_count, spec, state)

        messages = [
            {"role": "system", "content": "你是 NanoAgent 决策引擎。只返回 JSON。"},
            {"role": "user", "content": prompt},
        ]

        try:
            result = self.llm_client.structured_chat(messages, ThinkAction, temperature=0.7)
            logger.info(f"Think succeeded: {result.action}")
            return {
                "action": result.action,
                "tool": result.tool,
                "arguments": result.arguments or {},
                "thought": result.reason or "",
            }
        except Exception as e:
            logger.error(f"Think phase failed: {e}")
            return {
                "action": "continue",
                "tool": None,
                "arguments": {},
                "thought": f"Error: {e}",
            }

    def _build_prompt(
        self, task, context, observations, step_count, spec, state,
    ) -> str:
        """构建动态 prompt"""
        recent_obs = self._get_recent_observations(observations, max_items=3)

        prompt = REACT_THINK_PROMPT.format(
            current_step=step_count + 1,
            completed_steps=[s.get("step", 0) for s in observations],
            step_count=step_count,
            max_steps=getattr(self, "max_steps", 20),
            task_goal=spec.overall_goal if spec else task,
            recent_observations=recent_obs,
            requirements=state.get_requirements_summary() if state else "",
            available_tools=self.tool_registry.get_tool_descriptions()
            if self.tool_registry
            else "No tools available",
        )

        # 需求已确认时添加强制提示
        if state and state.is_requirements_confirmed():
            current_state = state.get_current_state().value
            prompt += (
                "\n\n【重要】需求已确认！不要再询问需求，"
                f"当前状态: {current_state}。必须开始执行，使用 write_file 创建文件。"
            )
            logger.info("需求已确认，添加强制提示")

        # 当前阶段约束
        if context.get("current_stage_spec"):
            prompt += f"\n\n【当前阶段约束】\n{context['current_stage_spec']}"

        # 已积累的决策和交付物
        decisions = context.get("accumulated_decisions", [])
        artifacts = context.get("accumulated_artifacts", [])
        if decisions:
            prompt += "\n\n【已确定的决策】\n" + "\n".join(
                f"{i}. {d[:150]}" for i, d in enumerate(decisions[-5:], 1)
            )
        if artifacts:
            prompt += "\n\n【已创建的交付物】\n" + "\n".join(f"- {a}" for a in artifacts)
            prompt += "\n⚠️ 不要重复创建上述已存在的文件！"

        # 禁止操作
        constraints = context.get("constraints", {})
        if isinstance(constraints, list):
            constraints = {"always": constraints, "never": []}
        if isinstance(constraints, dict) and constraints.get("never"):
            prompt += "\n【禁止操作】\n" + "\n".join(
                f"- {c}" for c in constraints["never"]
            )

        return prompt
