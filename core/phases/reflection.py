"""
Reflection 阶段处理器
"""

from typing import Dict, Any
from pydantic import BaseModel, Field
from loguru import logger

from .base import BasePhase
from core.prompt import REFLECTION_PROMPT
from domain.models.models import ReflectionResult


class ReflectionPhase(BasePhase):
    """Reflection 阶段"""

    def execute(
        self, execution_history: list, task_spec: Any = None,
        current_progress: Dict[str, Any] = None, **kwargs,
    ) -> Dict[str, Any]:
        logger.info("=== Reflection Phase ===")

        prompt = REFLECTION_PROMPT.format(
            execution_history=str(execution_history[-10:]),
            task_spec=str(task_spec) if task_spec else "No spec",
            current_progress=str(current_progress or {}),
        )

        messages = [
            {"role": "system", "content": "评估进度，返回 JSON。"},
            {"role": "user", "content": prompt},
        ]

        try:
            result = self.llm_client.structured_chat(messages, ReflectionResult, temperature=0.5)
            d = result.model_dump()
            logger.info(f"Reflection: task={d['task_completed']}, stage={d['stage_completed']}")
            return d
        except Exception as e:
            logger.error(f"Reflection failed: {e}")
            return {
                "task_completed": False, "stage_completed": False,
                "progress_summary": f"Failed: {e}", "issues_found": [str(e)],
                "next_action": "continue", "confidence_score": 0.0,
            }
