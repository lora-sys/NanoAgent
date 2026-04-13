"""目录列表工具"""

from pathlib import Path
from pydantic import BaseModel, Field
from loguru import logger
import os

# 安全沙箱目录
SANDBOX_DIR = Path(os.path.join(os.getcwd(), "agent_workspace")).resolve()
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)


class ListDirectoryInput(BaseModel):
    """列出目录输入"""

    path: str = Field(default=".", description="目录路径（相对于 agent_workspace）")


def safe_list_directory(path: str = ".") -> str:
    """安全列出目录内容"""
    try:
        # 处理绝对路径转换为相对路径
        if path.startswith(("/sandbox", "/project-root", "/project/", "/")):
            path = path.lstrip("/")
            for prefix in ["sandbox", "project-root/", "project/", "root/"]:
                if path.startswith(prefix):
                    path = path[len(prefix) :].lstrip("/")
                    break
            logger.info(f"Converted absolute path to relative: {path}")

        target = (SANDBOX_DIR / path).resolve()

        # 使用相对路径检查来验证沙箱边界
        try:
            target.relative_to(SANDBOX_DIR)
        except ValueError:
            raise ValueError(
                f"Access denied: Path outside sandbox. Requested: {path}, Resolved: {target}"
            )

        if not target.exists() or not target.is_dir():
            return f"Directory not found: {path}"

        items = []
        for item in target.iterdir():
            item_type = "DIR" if item.is_dir() else "FILE"
            items.append(f"[{item_type}] {item.name}")

        result = "\n".join(items) if items else "Directory is empty"
        logger.info(f"Listed directory: {path} ({len(items)} items)")
        return result
    except Exception as e:
        logger.error(f"Error listing directory {path}: {e}")
        return f"Error: {str(e)}"
