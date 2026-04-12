"""
通用工具函数

消除重复代码，提供共享工具函数。
包含时间戳获取、文本截断、观察记录摘要等常用功能。
"""

from datetime import datetime
from typing import List, Dict, Any


def get_timestamp() -> str:
    """获取当前时间戳（ISO 格式）。

    Returns:
        当前时间的 ISO 格式字符串，例如 "2023-10-27T10:00:00.123456"。

    Example:
        >>> ts = get_timestamp()
        >>> isinstance(ts, str)
        True
    """
    return datetime.now().isoformat()


def truncate_text(text: str, max_length: int = 200) -> str:
    """截断文本到指定长度。

    如果文本长度超过 `max_length`，则截断并在末尾添加 "..."。

    Args:
        text: 原始文本。
        max_length: 最大允许长度。

    Returns:
        截断后的文本。

    Example:
        >>> truncate_text("Hello World", 5)
        'Hello...'
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def get_recent_observations_summary(
    observations: List[Dict[str, Any]], max_items: int = 3
) -> str:
    """获取最近观察记录摘要。

    从观察记录列表中提取最近的几条记录，格式化为易读的字符串。

    Args:
        observations: 观察记录列表，每条记录应包含 'step', 'action', 'result'。
        max_items: 最多返回的条数。

    Returns:
        格式化的观察记录字符串。

    Example:
        >>> obs = [{"step": 1, "action": "write_file", "result": "OK"}]
        >>> get_recent_observations_summary(obs)
        '步骤 1: write_file -> OK'
    """
    if not observations:
        return "无观察记录"

    recent = (
        observations[-max_items:] if len(observations) > max_items else observations
    )
    summary_lines = []

    for obs in recent:
        step = obs.get("step", "?")
        action = obs.get("action", "unknown")
        result = obs.get("result", "")

        if isinstance(result, str):
            result = truncate_text(result, 200)
        else:
            result = str(result)[:200]

        summary_lines.append(f"步骤 {step}: {action} -> {result}")

    return "\n".join(summary_lines)
