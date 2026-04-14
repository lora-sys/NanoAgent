"""
上下文管理器 - 持久化阶段上下文
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger


class ContextManager:
    def __init__(self, context_dir: str = None):
        base = context_dir or os.path.join(os.getcwd(), ".spec", "context")
        self.context_dir = Path(base)
        self.context_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ContextManager initialized: {self.context_dir}")

    def _file_path(self, stage_id: str) -> Path:
        return self.context_dir / f"{stage_id}.json"

    def save_context(self, stage_id: str, data: Dict[str, Any]) -> None:
        path = self._file_path(stage_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Context saved: {stage_id}")

    def load_context(self, stage_id: str) -> Optional[Dict[str, Any]]:
        path = self._file_path(stage_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Context loaded: {stage_id}")
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load context: {e}")
            return None

    def update_context(self, stage_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = self.load_context(stage_id) or {}
        merged = self._deep_merge(existing, updates)
        self.save_context(stage_id, merged)
        return merged

    @staticmethod
    def _deep_merge(base: Dict, updates: Dict) -> Dict:
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], list) and isinstance(value, list):
                result[key] = list(dict.fromkeys(result[key] + value))
            elif key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ContextManager._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
