"""
持久化管理器 - 文件读写
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class PersistenceManager:
    def __init__(self, base_dir: str = ".spec"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        p = Path(path)
        return p if p.is_absolute() else self.base_dir / p

    def read_json(self, path: str) -> Any:
        with open(self._resolve(path), "r", encoding="utf-8") as f:
            return json.load(f)

    def write_json(self, path: str, data: Any, indent: int = 2) -> None:
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

    def read_text(self, path: str) -> str:
        with open(self._resolve(path), "r", encoding="utf-8") as f:
            return f.read()

    def write_text(self, path: str, content: str) -> None:
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)

    def exists(self, path: str) -> bool:
        return self._resolve(path).exists()

    def ensure_dir(self, path: str) -> Path:
        p = self._resolve(path)
        p.mkdir(parents=True, exist_ok=True)
        return p
