"""预置测试任务 fixtures — 可复用的标准化测试场景"""

from typing import Dict


# 工具测试任务
TOOL_TASKS: Dict[str, str] = {
    "grep_search": "在 core/ 目录下搜索包含 'def run' 的代码行",
    "grep_no_match": "在 core/ 目录下搜索 'XY_ZZZZ_NONEEXISTENT_12345'",
    "read_file": "读取 README.md 文件的内容",
    "list_files": "列出当前目录的文件",
    "file_edit": "将当前目录下的 README.md 第一行加上 # Updated 标记",
}

# Agent 行为测试任务
AGENT_TASKS: Dict[str, str] = {
    "simple_chat": "用一句话介绍 Python 编程语言",
    "async_concept": "什么是异步编程？",
    "router_analysis": "分析这个项目的核心模块结构",
}


def get_task(name: str) -> str:
    """获取预置任务，支持 raise。"""
    for pool in (TOOL_TASKS, AGENT_TASKS):
        if name in pool:
            return pool[name]
    raise ValueError(f"Unknown task fixture: {name}")
