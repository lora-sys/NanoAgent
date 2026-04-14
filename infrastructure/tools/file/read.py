"""读取文件工具"""

from pydantic import BaseModel, Field
from loguru import logger
from infrastructure.tools.file.utils import resolve_sandbox_path


class ReadFileInput(BaseModel):
    filepath: str = Field(..., description="文件路径（相对于 agent_workspace）")


def safe_read_file(filepath: str) -> str:
    """读取沙箱目录中的文件"""
    try:
        path = resolve_sandbox_path(filepath)
        if not path.exists():
            return f"Error: File not found: {filepath}"
        content = path.read_text(encoding="utf-8")
        logger.info(f"Read file: {filepath} ({len(content)} chars)")
        return content
    except Exception as e:
        return f"Error: {e}"
