"""Base phase handler."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from infrastructure.utils import get_recent_observations_summary, truncate_text


class BasePhase(ABC):
    def __init__(self, llm_client, tool_registry=None, config=None):
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.config = config or {}

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        ...

    def _get_recent_observations(self, observations, max_items=3):
        return get_recent_observations_summary(observations, max_items)
