"""Act 阶段处理器 - 执行工具调用"""

from typing import Dict, Any
from loguru import logger
import time

from .base import BasePhase
from domain.exceptions.exceptions import ToolError, ToolNotFoundError


class ActingPhase(BasePhase):
    """Act 阶段处理器"""

    def execute(self, action: Dict[str, Any], max_retries: int = 3) -> Any:
        """执行工具调用"""
        if action.get("action") != "tool_call":
            return {"status": "skipped", "reason": "Not a tool call"}

        tool_name = action.get("tool")
        if not tool_name or tool_name == "unknown":
            raise ToolNotFoundError("Unknown tool")

        logger.info(f"Executing tool: {tool_name}")
        arguments = action.get("arguments", {}).copy()

        return self._execute_with_retry(tool_name, arguments, max_retries)

    def _execute_with_retry(
        self, tool_name: str, arguments: Dict[str, Any], max_retries: int
    ) -> Any:
        """带重试的工具执行"""
        for attempt in range(max_retries):
            try:
                result = (
                    self.tool_registry.execute(tool_name, arguments)
                    if self.tool_registry
                    else f"Tool registry not available: {tool_name}"
                )
                if isinstance(result, str) and result.startswith("Error:"):
                    raise ToolError(tool_name, result)
                return result
            except ToolError:
                raise
            except Exception as e:
                if attempt == max_retries - 1:
                    raise ToolError(tool_name, str(e)) from e
                time.sleep(1 * (attempt + 1))
