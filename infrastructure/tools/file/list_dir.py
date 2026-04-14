"""列出目录工具"""

from pydantic import BaseModel, Field
from loguru import logger
from infrastructure.tools.file.utils import resolve_sandbox_path
import os


class ListDirectoryInput(BaseModel):
    path: str = Field(default=".", description="目录路径（相对于 agent_workspace）")


def safe_list_directory(path: str = ".") -> str:
    """列出沙箱目录内容"""
    try:
        full_path = resolve_sandbox_path(path)
        if not full_path.is_dir():
            return f"Error: Not a directory: {path}"
        items = os.listdir(full_path)
        result = "\n".join(f"- {item}" for item in sorted(items))
        logger.info(f"Listed directory: {path} ({len(items)} items)")
        return result
    except Exception as e:
        return f"Error: {e}"
