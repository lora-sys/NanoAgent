"""共享工具函数"""

import os
from pathlib import Path


SANDBOX_DIR = os.path.join(os.getcwd(), "agent_workspace")


def resolve_sandbox_path(filepath: str) -> Path:
    """解析沙箱文件路径，处理各种前缀"""
    path = filepath
    for prefix in ["/sandbox/", "/project-root/", "/agent_workspace/"]:
        if path.startswith(prefix):
            path = path[len(prefix):]
    for prefix in ["project-root/", "project/", "root/", "agent_workspace/"]:
        if path.startswith(prefix):
            path = path[len(prefix):]
    full = Path(os.path.join(SANDBOX_DIR, path))
    # 安全检查：确保最终路径在沙箱内
    full = full.resolve()
    sandbox = Path(SANDBOX_DIR).resolve()
    if not str(full).startswith(str(sandbox)):
        raise ValueError(f"Path escapes sandbox: {filepath}")
    return full
