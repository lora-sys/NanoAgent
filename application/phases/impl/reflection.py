"""
Reflection 阶段处理器

负责自我评估和进度检查
"""

from typing import Dict, Any
from pydantic import BaseModel, Field
from loguru import logger

from .base import BasePhase
from core.prompt import SYSTEM_PROMPT, REFLECTION_PROMPT


class ReflectionResult(BaseModel):
    """反思阶段的结构化输出"""

    task_completed: bool = Field(..., description="任务是否完成")
    stage_completed: bool = Field(..., description="阶段是否完成")
    progress_summary: str = Field(..., description="进度总结")
    issues_found: list[str] = Field(default_factory=list, description="发现的问题")
    solutions_applied: list[str] = Field(
        default_factory=list, description="应用的解决方案"
    )
    next_action: str = Field(..., description="下一步: 继续/调整策略/完成/请求帮助")
    confidence_score: float = Field(default=0.5, description="置信度 (0-1)")
    decisions: list[str] = Field(default_factory=list, description="关键决策列表")
    artifacts: list[str] = Field(default_factory=list, description="交付物列表")


class ReflectionPhase(BasePhase):
    """Reflection 阶段处理器"""

    def execute(
        self,
        execution_history: list,
        task_spec: Any,
        current_progress: Dict[str, Any],
        stage_success_criteria: list = None,
        rule_engine: Any = None,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        执行 Reflection 阶段

        Args:
            execution_history: 执行历史
            task_spec: 任务规范
            current_progress: 当前进度
            stage_success_criteria: 阶段成功标准
            rule_engine: 规则引擎
            context: 上下文字典

        Returns:
            反思结果
        """
        logger.info("=== Reflection Phase ===")

        # 构建 prompt
        prompt = REFLECTION_PROMPT.format(
            execution_history=str(execution_history[-10:]),  # 最近 10 条
            task_spec=str(task_spec) if task_spec else "No spec",
            current_progress=str(current_progress),
            stage_success_criteria=str(stage_success_criteria)
            if stage_success_criteria
            else "No criteria",
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            # 使用结构化输出
            result = self.llm_client.structured_chat_with_validation(
                messages,
                ReflectionResult,
                temperature=0.5,
            )

            result_dict = result.model_dump()
            logger.info(f"LLM 判断: stage_completed = {result_dict['stage_completed']}")

            # 使用规则引擎验证（如果可用）
            if rule_engine:
                safe_context = context or {}
                rule_result = rule_engine.check_stage_completion(
                    safe_context.get("current_stage_id", "unknown"),
                    result_dict.get("artifacts", []),
                    result_dict.get("decisions", []),
                )
                logger.info(f"规则引擎判断: stage_completed = {rule_result}")
                result_dict["rule_engine_completed"] = rule_result

                # 综合判断
                result_dict["stage_completed"] = (
                    result_dict["stage_completed"] or rule_result
                )

            logger.info(f"最终判断: stage_completed = {result_dict['stage_completed']}")
            return result_dict

        except Exception as e:
            logger.error(f"Reflection phase failed: {e}")
            return {
                "task_completed": False,
                "stage_completed": False,
                "progress_summary": f"Reflection failed: {str(e)}",
                "issues_found": [str(e)],
                "next_action": "继续",
                "confidence_score": 0.0,
            }
