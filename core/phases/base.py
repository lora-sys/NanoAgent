"""
阶段处理器基类

所有阶段处理器（Thinking, Acting, Observing 等）的公共基类，
提供通用功能如文本截断、JSON 解析、观察记录摘要等。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from loguru import logger
from core.utils import get_recent_observations_summary, truncate_text


class BasePhase(ABC):
    """阶段处理器抽象基类。

    定义了所有阶段处理器必须实现的 `execute` 方法，
    并提供通用的辅助方法。

    Attributes:
        llm_client: LLM 客户端实例。
        tool_registry: 工具注册表实例。
        config: 配置字典。
    """

    def __init__(self, llm_client: Any, tool_registry: Optional[Any] = None, config: Optional[Dict[str, Any]] = None):
        """初始化阶段处理器。

        Args:
            llm_client: LLM 客户端，用于与语言模型交互。
            tool_registry: 工具注册表，用于管理和执行工具。
            config: 配置字典，包含阶段特定的配置项。
        """
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.config = config or {}

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行阶段逻辑。

        子类必须实现此方法以定义具体的阶段行为。

        Args:
            **kwargs: 阶段执行所需的参数。

        Returns:
            执行结果字典。
        """
        pass

    def _truncate_text(self, text: str, max_length: int = 1000) -> str:
        """截断文本到指定长度。

        Args:
            text: 原始文本。
            max_length: 最大长度。

        Returns:
            截断后的文本。
        """
        return truncate_text(text, max_length)

    def _safe_json_parse(self, text: str) -> Optional[Dict]:
        """安全解析 JSON，失败返回 None。

        Args:
            text: 包含 JSON 的字符串。

        Returns:
            解析后的字典，如果失败则返回 None。
        """
        import json
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return None

    def _get_recent_observations(
        self, observations: List[Dict[str, Any]], max_items: int = 3
    ) -> str:
        """获取最近的观察记录摘要。

        Args:
            observations: 观察记录列表。
            max_items: 返回的最大记录数。

        Returns:
            格式化的观察记录字符串。
        """
        return get_recent_observations_summary(observations, max_items)
