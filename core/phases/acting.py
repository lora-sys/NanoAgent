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

        # 防御：阻止写入纯状态记录文件（防止 Agent 陷入写状态文件的死循环）
        if tool_name in ("safe_write_file", "write_file"):
            filepath = arguments.get("filepath", "")
            content = arguments.get("content", "")
            # 检查是否是纯状态描述文件（无实质代码内容）
            if self._is_status_file(filepath, content):
                logger.warning(
                    f"Blocked status file write: {filepath}. "
                    f"Agent should create real project files instead."
                )
                return (
                    f"⚠️ 已阻止写入状态文件: {filepath}。\n"
                    f"请创建实际的项目文件（代码、文档、配置），而不是记录当前状态。"
                )
            # 检查是否重复覆盖已有文件
            dup_result = self._check_duplicate_write(filepath, content)
            if dup_result:
                logger.warning(f"Duplicate file write blocked: {filepath}")
                return dup_result

        # 特殊处理：ask_user_question 的 questions 数组转字符串
        if tool_name == "ask_user_question":
            arguments = self._handle_ask_user_question(arguments)

        # 执行工具，带重试
        return self._execute_with_retry(tool_name, arguments, max_retries)

    def _is_status_file(self, filepath: str, content: str) -> bool:
        """检查文件是否是纯状态描述文件。

        如果文件名和内容都只是记录状态而无实质代码，返回 True。
        """
        status_keywords = [
            "stage_1_requirements",
            "stage_2_",
            "stage_3_",
            "requirements_status",
            "requirements_checklist",
            "requirements_summary",
            "requirements_complete",
            "requirements_confirmed",
            "artifact_summary",
            "artifact_log",
            "status.json",
            "_status.txt",
        ]

        fp_lower = filepath.lower()

        # 文件名包含状态关键词
        if any(kw in fp_lower for kw in status_keywords):
            return True

        # 内容以 JSON 形式记录状态（包含 "stage", "status", "REQUIREMENT" 等）
        content_stripped = content.strip()
        if content_stripped.startswith("{") and content_stripped.endswith("}"):
            status_fields = [
                '"stage"',
                '"status"',
                '"current_state"',
                "REQUIREMENT_GATHERING",
                "REQUIREMENT_CONFIRMED",
            ]
            if any(field in content for field in status_fields):
                # 排除 package.json, tsconfig.json 等真实配置文件
                if filepath.endswith(".json") and not any(
                    kw in fp_lower
                    for kw in ["package.json", "tsconfig", "babel", "eslint", "webpack"]
                ):
                    return True

        return False

    def _check_duplicate_write(self, filepath: str, content: str) -> Optional[str]:
        """检查是否重复覆盖已有文件。
        
        如果文件已存在且内容差异很小（说明 Agent 在反复写同一个文件），则阻止。
        
        Returns:
            如果是重复写入，返回阻止消息；否则返回 None。
        """
        import os
        from difflib import SequenceMatcher
        
        SANDBOX_DIR = self._get_sandbox_dir()
        full_path = os.path.join(SANDBOX_DIR, filepath)
        
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    existing_content = f.read()
                
                # 计算内容相似度
                similarity = SequenceMatcher(None, existing_content, content).ratio()
                
                # 如果内容 90% 以上相同，认为是重复覆盖
                if similarity > 0.9:
                    return (
                        f"⚠️ 文件 {filepath} 已存在且内容基本相同（相似度 {similarity:.0%}）。\n"
                        f"请创建新的文件或扩展现有文件的功能，而不是反复覆盖同一文件。"
                    )
            except Exception:
                pass  # 读取失败时不阻止写入
        
        return None

    def _get_sandbox_dir(self) -> str:
        """获取沙箱目录路径"""
        import os
        from pathlib import Path
        return str(Path(os.path.join(os.getcwd(), "agent_workspace")).resolve())

    def _map_parameters(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
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
                        [f"{i + 1}. {q}" for i, q in enumerate(questions)]
                    )
                    logger.info(
                        f"Converted {len(questions)} questions to single string"
                    )
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
                        logger.info(
                            f"Tool execution succeeded after {attempt + 1} attempts"
                        )
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
