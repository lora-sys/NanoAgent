"""
通用工具函数

消除重复代码，提供共享工具函数
"""

from datetime import datetime
from typing import List, Dict, Any, Optional


def get_timestamp() -> str:
    """获取当前时间戳 ISO 格式"""
    return datetime.now().isoformat()


def truncate_text(text: str, max_length: int = 200) -> str:
    """截断文本到指定长度"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def get_recent_observations_summary(
    observations: List[Dict[str, Any]], max_items: int = 3
) -> str:
    """
    获取最近观察记录摘要
    
    Args:
        observations: 观察记录列表
        max_items: 最多返回条数
        
    Returns:
        格式化的观察记录字符串
    """
    if not observations:
        return "无观察记录"
    
    recent = observations[-max_items:] if len(observations) > max_items else observations
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
