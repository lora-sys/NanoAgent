"""文件读取工具"""
from pathlib import Path
from pydantic import BaseModel, Field
from loguru import logger
import os

# 安全沙箱目录
SANDBOX_DIR = Path(os.path.join(os.getcwd(), "agent_workspace")).resolve()
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

class ReadFileInput(BaseModel):
    """读取文件输入"""
    filepath: str = Field(..., description="文件路径（相对于 agent_workspace，例如：'main.py'）")

def safe_read_file(filepath: str) -> str:
    """安全读取文件（限制在沙箱目录）"""
    try:
        target = (SANDBOX_DIR / filepath).resolve()
        if not str(target).startswith(str(SANDBOX_DIR)):
            raise ValueError("Access denied: Path outside sandbox")
        if not target.exists():
            return f"File not found: {filepath}"
        content = target.read_text(encoding="utf-8")
        logger.info(f"Read file: {filepath} ({len(content)} chars)")
        return content
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return f"Error: {str(e)}"