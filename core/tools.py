# core/tools.py  (新增部分)
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger
import os

# 安全沙箱目录（所有文件操作都限制在这里）
# 使用绝对路径确保路径解析正确
SANDBOX_DIR = Path(os.path.join(os.getcwd(), "agent_workspace")).resolve()
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"Sandbox directory initialized: {SANDBOX_DIR}")

class ReadFileInput(BaseModel):
    """读取文件输入"""
    filepath: str = Field(..., description="文件路径（相对于 agent_workspace）")

class WriteFileInput(BaseModel):
    """写入文件输入"""
    filepath: str = Field(..., description="文件路径（相对于 agent_workspace）")
    content: str = Field(..., description="要写入的内容")
    mode: str = Field(default="w", description="写入模式：w=覆盖, a=追加")

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

def safe_write_file(filepath: str, content: str, mode: str = "w") -> str:
    """安全写入文件（限制在沙箱目录）"""
    try:
        target = (SANDBOX_DIR / filepath).resolve()
        if not str(target).startswith(str(SANDBOX_DIR)):
            raise ValueError("Access denied: Path outside sandbox")
        
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, mode, encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Wrote file: {filepath} ({len(content)} chars)")
        return f"✅ Successfully wrote {len(content)} chars to {filepath}"
    except Exception as e:
        logger.error(f"Error writing file {filepath}: {e}")
        return f"Error: {str(e)}"

# 扩展工具集合 - 可根据需要添加更多工具
class ListDirectoryInput(BaseModel):
    """列出目录输入"""
    path: str = Field(default=".", description="目录路径（相对于 agent_workspace）")

def safe_list_directory(path: str = ".") -> str:
    """安全列出目录内容"""
    try:
        target = (SANDBOX_DIR / path).resolve()
        if not str(target).startswith(str(SANDBOX_DIR)):
            raise ValueError("Access denied: Path outside sandbox")
        
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

# 工具注册辅助函数
def get_tool_registry() -> dict:
    """获取所有可用工具的注册信息"""
    return {
        "read_file": {
            "function": safe_read_file,
            "description": "读取文件内容（限制在 agent_workspace 目录）",
            "schema": ReadFileInput.model_json_schema()
        },
        "write_file": {
            "function": safe_write_file,
            "description": "写入文件内容（限制在 agent_workspace 目录，支持覆盖和追加模式）",
            "schema": WriteFileInput.model_json_schema()
        },
        "list_directory": {
            "function": safe_list_directory,
            "description": "列出目录内容（限制在 agent_workspace 目录）",
            "schema": ListDirectoryInput.model_json_schema()
        }
    }