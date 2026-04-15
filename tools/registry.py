"""工具注册表 - 精简版"""

import inspect
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List

from exceptions import ToolError

SANDBOX_DIR = Path.cwd() / "agent_workspace"


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, func: Callable, description: str = ""):
        self._tools[name] = {
            "function": func,
            "description": description or (func.__doc__ or "").strip(),
            "schema": _build_schema(func),
        }

    def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        tool = self._tools.get(name)
        if not tool:
            raise ToolError(name, f"Tool not found: {name}")

        # 参数映射：处理常见的参数名差异
        mapped_args = self._map_arguments(name, arguments)

        try:
            return tool["function"](**mapped_args)
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(name, str(e)) from e

    def _map_arguments(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """映射参数名，处理常见的参数名差异"""
        param_mappings = {
            "read_file": {"path": "filename", "absolute_path": "filename"},
            "list_files": {},
            "edit_file": {},
            "run_bash": {},
        }

        mapping = param_mappings.get(tool_name, {})
        return {mapping.get(key, key): value for key, value in arguments.items()}

    def get_tool_descriptions(self) -> str:
        lines = []
        for name, t in self._tools.items():
            lines.append(f"- {name}: {t['description']}")
            props = t.get("schema", {}).get("properties", {})
            required = t.get("schema", {}).get("required", [])
            lines.extend(
                f"  - {pname}: {pinfo.get('type', 'string')}"
                f"{' (必需)' if pname in required else f\" (默认: {pinfo.get('default', '无')})\"}"
                f" - {pinfo.get('description', '')}"
                for pname, pinfo in props.items()
            )
        return "\n".join(lines)

    def get_tool_list(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": t["description"],
                    "parameters": {
                        "type": "object",
                        "properties": t["schema"].get("properties", {}),
                        "required": t["schema"].get("required", []),
                    },
                },
            }
            for name, t in self._tools.items()
        ]


_registry: ToolRegistry = None


def get_tool_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _register_tools(_registry)
    return _registry


def _build_schema(func: Callable) -> dict:
        sig = inspect.signature(func)
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }

        properties = {
            name: {
                "type": type_map.get(
                    param.annotation if param.annotation != inspect.Parameter.empty else str,
                    "string"
                ),
                "description": "",
            }
            for name, param in sig.parameters.items()
            if name not in ("cls", "self")
        }

        required = [
            name
            for name, param in sig.parameters.items()
            if name not in ("cls", "self") and param.default == inspect.Parameter.empty
        ]

        for name, param in sig.parameters.items():
            if name not in ("cls", "self") and param.default != inspect.Parameter.empty:
                properties[name]["default"] = param.default

        return {"properties": properties, "required": required}

def _resolve_path(filepath: str) -> Path:
    path = Path(filepath)
    if not path.is_absolute():
        # 相对于当前工作目录，而不是 SANDBOX_DIR
        path = Path.cwd() / path
    return path.resolve()


def _register_tools(registry: ToolRegistry):
    def read_file(filename: str) -> Dict[str, Any]:
        """Gets the full content of a file."""
        path = _resolve_path(filename)
        if not path.exists():
            return {
                "file_path": str(path),
                "content": f"Error: File not found: {filename}",
            }
        return {"file_path": str(path), "content": path.read_text(encoding="utf-8")}

    def list_files(path: str = ".") -> Dict[str, Any]:
        """Lists the files in a directory."""
        full_path = _resolve_path(path)
        if not full_path.is_dir():
            return {"path": str(full_path), "files": f"Error: Not a directory: {path}"}
        return {
            "path": str(full_path),
            "files": [
                {"filename": item.name, "type": "file" if item.is_file() else "dir"}
                for item in sorted(full_path.iterdir())
            ],
        }

    def edit_file(path: str, old_str: str, new_str: str) -> Dict[str, Any]:
        """Replaces first occurrence of old_str with new_str in file."""
        full_path = _resolve_path(path)
        if not old_str:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(new_str, encoding="utf-8")
            return {"path": str(full_path), "action": "created_file"}

        if not full_path.exists():
            return {"path": str(full_path), "action": "file_not_found"}

        original = full_path.read_text(encoding="utf-8")
        if old_str not in original:
            return {"path": str(full_path), "action": "old_str_not_found"}

        edited = original.replace(old_str, new_str, 1)
        full_path.write_text(edited, encoding="utf-8")
        return {"path": str(full_path), "action": "edited"}

    def run_bash(command: str, timeout: int = 60) -> str:
        """Executes bash command in sandbox."""
        if not command or not command.strip():
            return "Error: Command is empty"

        forbidden = ["rm -rf /", "sudo", "dd", "mkfs", ":(){:|:&};:"]
        if any(d in command.lower() for d in forbidden):
            return "Error: Command blocked by security policy"

        SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=SANDBOX_DIR,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = (result.stdout or "") + (
                f"\n{result.stderr}" if result.stderr else ""
            )
            if len(output) > 4000:
                output = output[:4000] + f"\n... [truncated, {len(output)} chars]"
            return f"[exit code: {result.returncode}]\n{output}".strip()
        except subprocess.TimeoutExpired:
            return f"Error: Command timeout ({timeout}s)"
        except Exception as e:
            return f"Error: {e}"

    registry.register("read_file", read_file, "Gets the full content of a file")
    registry.register("list_files", list_files, "Lists the files in a directory")
    registry.register(
        "edit_file",
        edit_file,
        "Replaces first occurrence of old_str with new_str in file",
    )
    registry.register("run_bash", run_bash, "Executes bash command in sandbox")
