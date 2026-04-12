"""Act phase handler - executes tool calls."""

from typing import Dict, Any, Optional
from loguru import logger
import time
import os
from pathlib import Path
from difflib import SequenceMatcher

from .base import BasePhase
from core.exceptions import ToolError, ToolNotFoundError


class ActingPhase(BasePhase):
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

    def execute(self, action: Dict[str, Any], max_retries: int = 3) -> Any:
        if action.get("action") != "tool_call":
            return {"status": "skipped", "reason": "Not a tool call"}
        tool_name = action.get("tool")
        if not tool_name or tool_name == "unknown":
            raise ToolNotFoundError("Unknown tool")
        logger.info(f"Executing tool: {tool_name}")
        arguments: Dict[str, Any] = action.get("arguments", {}).copy()
        arguments = self._map_parameters(tool_name, arguments)
        if tool_name in ("safe_write_file", "write_file"):
            filepath, content = (
                arguments.get("filepath", ""),
                arguments.get("content", ""),
            )
            if self._is_status_file(filepath, content):
                return f"⚠️ 已阻止写入状态文件: {filepath}。请创建实际项目文件。"
            dup = self._check_duplicate_write(filepath, content)
            if dup:
                return dup
        if tool_name == "ask_user_question":
            arguments = self._handle_ask_user_question(arguments)
        return self._execute_with_retry(tool_name, arguments, max_retries)

    def _map_parameters(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        if tool_name not in self.PARAM_MAPPINGS:
            return arguments
        for target, sources in self.PARAM_MAPPINGS[tool_name].items():
            if target not in arguments:
                for src in sources:
                    if src in arguments:
                        arguments[target] = arguments.pop(src)
                        break
        return arguments

    def _handle_ask_user_question(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if "question" not in arguments:
            qs = arguments.pop("questions", [])
            arguments["question"] = (
                "\n".join(f"{i + 1}. {q}" for i, q in enumerate(qs))
                if qs
                else "请提供更多信息"
            )
        return arguments

    def _execute_with_retry(
        self, tool_name: str, arguments: Dict[str, Any], max_retries: int
    ) -> Any:
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

    def _is_status_file(self, filepath: str, content: str) -> bool:
        keywords = [
            "stage_1_requirements",
            "stage_2_",
            "requirements_status",
            "requirements_checklist",
            "requirements_summary",
            "requirements_confirmed",
            "artifact_summary",
            "status.json",
        ]
        fp = filepath.lower()
        if any(kw in fp for kw in keywords):
            return True
        c = content.strip()
        if (
            c.startswith("{")
            and c.endswith("}")
            and any(
                f in content for f in ['"stage"', '"status"', "REQUIREMENT_GATHERING"]
            )
        ):
            return fp.endswith(".json") and not any(
                k in fp for k in ["package.json", "tsconfig", "babel", "eslint"]
            )
        return False

    def _check_duplicate_write(self, filepath: str, content: str) -> Optional[str]:
        full = Path(os.path.join(os.getcwd(), "agent_workspace"), filepath)
        if full.exists():
            try:
                existing = full.read_text(encoding="utf-8")
                if SequenceMatcher(None, existing, content).ratio() > 0.9:
                    return f"⚠️ 文件 {filepath} 已存在且内容基本相同。请创建新文件或扩展现有功能。"
            except Exception:
                pass
        return None

    def _get_sandbox_dir(self) -> str:
        return str(Path(os.path.join(os.getcwd(), "agent_workspace")).resolve())
