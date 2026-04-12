"""文件写入工具"""

from pathlib import Path
from pydantic import BaseModel, Field
from loguru import logger
import os

# 安全沙箱目录
SANDBOX_DIR = Path(os.path.join(os.getcwd(), "agent_workspace")).resolve()
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)


class WriteFileInput(BaseModel):
    """写入文件输入"""

    filepath: str = Field(
        ..., description="文件路径（相对于 agent_workspace，例如：'main.py'）"
    )
    content: str = Field(..., description="要写入的内容")
    mode: str = Field(default="w", description="写入模式：w=覆盖, a=追加")


def safe_write_file(filepath: str, content: str, mode: str = "w") -> str:
    """安全写入文件（限制在沙箱目录）"""
    try:
        # 处理绝对路径转换为相对路径
        # 如果路径以 /project-root/ 或其他绝对路径开头，转换为相对路径
        if filepath.startswith(("/project-root/", "/project/", "/")):
            # 提取相对路径部分
            filepath = filepath.lstrip("/")
            # 移除常见的前缀
            for prefix in ["project-root/", "project/", "root/"]:
                if filepath.startswith(prefix):
                    filepath = filepath[len(prefix) :]
                    break
            logger.info(f"Converted absolute path to relative: {filepath}")

        target = (SANDBOX_DIR / filepath).resolve()

        # 使用相对路径检查来验证沙箱边界
        try:
            target.relative_to(SANDBOX_DIR)
        except ValueError:
            raise ValueError(
                f"Access denied: Path outside sandbox. Requested: {filepath}, Resolved: {target}"
            )

        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, mode, encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Wrote file: {filepath} ({len(content)} chars)")
        return f"✅ Successfully wrote {len(content)} chars to {filepath}"
    except Exception as e:
        logger.error(f"Error writing file {filepath}: {e}")
        return f"Error: {str(e)}"
