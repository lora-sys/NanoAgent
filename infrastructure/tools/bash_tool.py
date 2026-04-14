"""Bash/Shell 执行工具"""

import subprocess
import os
from pydantic import BaseModel, Field
from loguru import logger

# 安全配置
ALLOWED_COMMANDS = {
    # 文件操作
    "ls", "cat", "head", "tail", "wc", "find", "tree",
    # 开发工具
    "python", "python3", "node", "npm", "uv", "pip", "git",
    # 系统信息
    "echo", "pwd", "date", "whoami", "uname",
    # 网络
    "curl", "wget",
}

DANGEROUS_COMMANDS = {
    "rm -rf /", "sudo", "dd", "mkfs",
    "> /dev/sda", ":(){:|:&};:",  # fork bomb
}

SANDBOX_DIR = os.path.join(os.getcwd(), "agent_workspace")


class BashInput(BaseModel):
    """执行 bash 命令输入"""
    command: str = Field(..., description="要执行的 shell 命令")
    timeout: int = Field(default=60, description="超时时间（秒）")


def run_bash(command: str, timeout: int = 60, cwd: str = None) -> str:
    """
    在沙箱内执行 bash 命令。

    Args:
        command: 要执行的命令
        timeout: 超时时间（秒），默认 60
        cwd: 工作目录，默认 sandbox 目录

    Returns:
        执行结果（stdout + stderr）
    """
    if not command or not command.strip():
        return "Error: 命令为空"

    work_dir = cwd or SANDBOX_DIR
    os.makedirs(work_dir, exist_ok=True)

    # 安全检查 1: 黑名单检查
    cmd_lower = command.lower().strip()
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous in cmd_lower:
            logger.warning(f"🚫 拒绝危险命令: {command}")
            return f"Error: 命令被安全策略拒绝（危险命令）"

    # 安全检查 2: 路径限制 - 不允许访问 sandbox 外的目录
    if "cd " in command:
        parts = command.split("cd ", 1)
        if len(parts) > 1:
            target = parts[1].strip().split()[0].strip("\"'")
            if not os.path.isabs(target):
                target = os.path.join(work_dir, target)
            resolved = os.path.realpath(target)
            if not resolved.startswith(os.path.realpath(SANDBOX_DIR)):
                logger.warning(f"🚫 拒绝访问 sandbox 外目录: {target}")
                return f"Error: 不允许访问 sandbox 外的目录: {target}"

    try:
        logger.info(f"🔧 执行: {command}")
        result = subprocess.run(
            command,
            shell=True,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            if output:
                output += "\n"
            output += result.stderr

        exit_code = result.returncode
        logger.info(f"执行完成 (exit={exit_code}): {len(output)} 字符输出")

        if output:
            # 截断过长输出
            max_output = 4000
            if len(output) > max_output:
                output = output[:max_output] + f"\n\n... [输出已截断，共 {len(output)} 字符]"

        return f"[exit code: {exit_code}]\n{output}".strip()

    except subprocess.TimeoutExpired:
        logger.warning(f"⏱️ 命令超时: {command}")
        return f"Error: 命令执行超时（{timeout}秒）"
    except Exception as e:
        logger.error(f"执行失败: {e}")
        return f"Error: {str(e)}"
