"""
Observe 阶段处理器

负责分析工具执行结果并决定下一步
"""

from typing import Dict, Any
from loguru import logger

from .base import BasePhase
from core.prompt import SYSTEM_PROMPT, REACT_OBSERVE_PROMPT


class ObservingPhase(BasePhase):
    """Observe 阶段处理器"""

    def execute(
        self,
        last_action: Dict[str, Any],
        tool_result: Any,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        执行 Observe 阶段

        Args:
            last_action: 上一步行动
            tool_result: 工具执行结果
            context: 上下文字典

        Returns:
            观察结果和下一步决策
        """
        logger.info("=== Observe Phase ===")

        # 格式化结果
        result_str = (
            str(tool_result) if not isinstance(tool_result, str) else tool_result
        )
        result_str = self._truncate_text(result_str, 1000)

        # 构建 prompt
        prompt = REACT_OBSERVE_PROMPT.format(
            last_action=str(last_action),
            tool_result=result_str,
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            # 使用普通 chat（观察阶段不需要结构化输出）
            response = self.llm_client.chat(messages, temperature=0.5)

            # 解析响应
            return self._parse_observe_response(response)

        except Exception as e:
            logger.error(f"Observe phase failed: {e}")
            return {
                "action": "continue",
                "thought": f"Observe failed: {str(e)}",
            }

    def _parse_observe_response(self, response: str) -> Dict[str, Any]:
        """解析 Observe 响应"""
        import json

        # 尝试提取 JSON
        if "{" in response and "}" in response:
            try:
                start = response.find("{")
                end = response.rfind("}") + 1
                data = json.loads(response[start:end])
                return data
            except Exception:
                pass

        # 回退：检查特殊标记
        if "TASK_COMPLETE" in response:
            return {"action": "complete", "reason": "Task completed"}
        elif "WAIT_FOR_USER" in response:
            return {"action": "wait", "reason": "Needs user input"}

        # 默认继续
        return {
            "action": "continue",
            "thought": response[:200],
        }
