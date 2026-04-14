"""写入文件工具"""

from pydantic import BaseModel, Field
from loguru import logger
from infrastructure.tools.file.utils import resolve_sandbox_path


class WriteFileInput(BaseModel):
    filepath: str = Field(..., description="文件路径（相对于 agent_workspace）")
    content: str = Field(..., description="要写入的内容")
    mode: str = Field(default="w", description="写入模式: w=覆盖, a=追加")


def safe_write_file(filepath: str, content: str, mode: str = "w") -> str:
    """写入文件到沙箱目录"""
    try:
        path = resolve_sandbox_path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, mode, encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Wrote file: {filepath} ({len(content)} chars)")
        return f"Successfully wrote {len(content)} chars to {filepath}"
    except Exception as e:
        return f"Error: {e}"
