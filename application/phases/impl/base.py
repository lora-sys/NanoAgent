"""
阶段处理器基类

所有阶段处理器的公共基类，提供通用功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.utils import get_recent_observations_summary, truncate_text


class BasePhase(ABC):
    """阶段处理器基类"""

    def __init__(self, llm_client, tool_registry=None, config=None):
        """
        初始化阶段处理器

        Args:
            llm_client: LLM 客户端
            tool_registry: 工具注册表
            config: 配置字典
        """
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.config = config or {}

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行阶段

        Args:
            **kwargs: 阶段特定参数

        Returns:
            执行结果字典
        """
        pass

    def _truncate_text(self, text: str, max_length: int = 1000) -> str:
        """截断文本到指定长度"""
        return truncate_text(text, max_length)

    def _safe_json_parse(self, text: str) -> Optional[Dict]:
        """安全解析 JSON，失败返回 None"""
        import json

        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return None

    def _get_recent_observations(self, observations: list, max_items: int = 3) -> str:
        """获取最近的观察记录摘要"""
        return get_recent_observations_summary(observations, max_items)
