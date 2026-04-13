"""Base phase handler."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from core.utils import get_recent_observations_summary, truncate_text


class BasePhase(ABC):
    def __init__(self, llm_client, tool_registry=None, config=None):
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.config = config or {}

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]: ...

    def _truncate_text(self, text: str, max_length: int = 1000) -> str:
        return truncate_text(text, max_length)

    def _safe_json_parse(self, text: str) -> Optional[Dict]:
        import json

        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return None

    def _get_recent_observations(
        self, observations: List[Dict[str, Any]], max_items: int = 3
    ) -> str:
        return get_recent_observations_summary(observations, max_items)
