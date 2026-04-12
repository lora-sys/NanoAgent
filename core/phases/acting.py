"""
Act 阶段处理器

负责执行工具调用
"""

from typing import Dict, Any, Optional
from loguru import logger
import time

from .base import BasePhase
from core.exceptions import ToolError, ToolNotFoundError


class ActingPhase(BasePhase):
    """Act 阶段处理器"""
    
    # 工具参数映射（应该在工具定义时声明，这里作为临时方案）
    PARAM_MAPPINGS: Dict[str, Dict[str, list]] = {
        "write_file": {
            "filepath": ["path", "file_path", "filename", "file"],
            "content": ["text", "data", "body"],
            "mode": ["write_mode", "file_mode"],
        },
        "read_file": {
            "filepath": ["path", "file_path", "filename", "file"],
            "offset": ["start_line", "from_line"],
            "limit": ["max_lines", "line_count"],
        },
        "list_directory": {
            "path": ["directory", "dir", "folder"],
            "ignore": ["ignore_patterns", "exclude", "skip"],
        },
        "safe_write_file": {
            "filepath": ["path", "file_path", "filename", "file"],
            "content": ["text", "data", "body"],
            "mode": ["write_mode", "file_mode"],
        },
        "safe_read_file": {
            "filepath": ["path", "file_path", "filename", "file"],
            "offset": ["start_line", "from_line"],
            "limit": ["max_lines", "line_count"],
        },
        "safe_list_directory": {
            "path": ["directory", "dir", "folder"],
            "ignore": ["ignore_patterns", "exclude", "skip"],
        },
        "ask_user_question": {
            "question": ["questions", "query", "text", "prompt"],
            "options": ["choices", "answers", "possible_answers"],
        },
    }
    
    def execute(
        self,
        action: Dict[str, Any],
        max_retries: int = 3,
    ) -> Any:
        """
        执行 Act 阶段
        
        Args:
            action: 动作描述
            max_retries: 最大重试次数
            
        Returns:
            执行结果
        """
        if action.get("action") != "tool_call":
            return {"status": "skipped", "reason": "Not a tool call"}
        
        tool_name = action.get("tool")
        if not tool_name or tool_name == "unknown":
            raise ToolNotFoundError("Unknown tool")
        
        logger.info(f"Executing tool: {tool_name}")
        
        arguments: Dict[str, Any] = action.get("arguments", {}).copy()
        
        # 应用参数映射
        arguments = self._map_parameters(tool_name, arguments)
        
        # 特殊处理：ask_user_question 的 questions 数组转字符串
        if tool_name == "ask_user_question":
            arguments = self._handle_ask_user_question(arguments)
        
        # 执行工具，带重试
        return self._execute_with_retry(tool_name, arguments, max_retries)
    
    def _map_parameters(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """应用参数映射规则"""
        if tool_name not in self.PARAM_MAPPINGS:
            return arguments
        
        mappings = self.PARAM_MAPPINGS[tool_name]
        for target_param, source_params in mappings.items():
            if target_param not in arguments:
                for source_param in source_params:
                    if source_param in arguments:
                        arguments[target_param] = arguments.pop(source_param)
                        logger.info(
                            f"Mapped '{source_param}' to '{target_param}' for {tool_name}"
                        )
                        break
        
        return arguments
    
    def _handle_ask_user_question(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """特殊处理：ask_user_question 的 questions 数组转字符串"""
        if "question" not in arguments:
            if "questions" in arguments and isinstance(arguments["questions"], list):
                questions = arguments.pop("questions")
                if len(questions) > 0:
                    arguments["question"] = "\n".join(
                        [f"{i+1}. {q}" for i, q in enumerate(questions)]
                    )
                    logger.info(f"Converted {len(questions)} questions to single string")
                else:
                    arguments["question"] = "请提供更多信息"
            elif "questions" in arguments:
                arguments["question"] = str(arguments.pop("questions"))
        
        return arguments
    
    def _execute_with_retry(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        max_retries: Optional[int] = 3,
    ) -> Any:
        """带重试的工具执行"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if not self.tool_registry:
                    return f"Tool registry not available: {tool_name}"
                
                result = self.tool_registry.execute(tool_name, arguments)
                
                # 检查结果是否为错误
                if isinstance(result, str) and result.startswith("Error:"):
                    raise ToolError(tool_name, result)
                
                if result:
                    if attempt > 0:
                        logger.info(f"Tool execution succeeded after {attempt + 1} attempts")
                    return result
                
            except ToolError:
                # 重新抛出 ToolError
                raise
            except Exception as e:
                last_error = e
                logger.warning(f"Tool execution attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(1 * (attempt + 1))
        
        # 所有重试失败
        error_msg = f"Tool execution failed after {max_retries} attempts: {last_error}"
        logger.error(error_msg)
        raise ToolError(tool_name, str(last_error)) from last_error
