"""File-backed store — JSON-based preference memory."""

import json
from pathlib import Path
from typing import Any, Dict

from core.memory.interfaces import PreferenceMemory


def _get_prefs_dir() -> Path:
    """Get preferences directory path."""
    prefs_dir = Path.home() / ".nanoagent" / "prefs"
    prefs_dir.mkdir(parents=True, exist_ok=True)
    return prefs_dir


class FileBackedMemoryStore(PreferenceMemory):
    """
    JSON file-based preference store at ~/.nanoagent/prefs/.
    Each preference key is a separate JSON file for easy management.
    """

    def __init__(self):
        self._prefs_dir = _get_prefs_dir()
        self._cache: Dict[str, Any] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load all preferences into cache on init."""
        if not self._prefs_dir.exists():
            return
        for f in self._prefs_dir.glob("*.json"):
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    key = f.stem
                    self._cache[key] = data
            except (json.JSONDecodeError, IOError):
                pass

    def _get_path(self, key: str) -> Path:
        return self._prefs_dir / f"{key}.json"

    def get_preference(self, key: str, default: Any = None) -> Any:
        val = self._cache.get(key)
        if val is not None:
            return val.get("value", default)
        # Try to load from disk
        path = self._get_path(key)
        if path.exists():
            try:
                with open(path) as fp:
                    data = json.load(fp)
                    self._cache[key] = data
                    return data.get("value", default)
            except (json.JSONDecodeError, IOError):
                pass
        return default

    def set_preference(self, key: str, value: Any) -> None:
        import datetime

        data = {
            "key": key,
            "value": value,
            "updated_at": datetime.datetime.now().isoformat(),
        }
        self._cache[key] = data
        path = self._get_path(key)
        with open(path, "w") as fp:
            json.dump(data, fp, indent=2)

    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all preferences as dict."""
        result = {}
        for key, data in self._cache.items():
            result[key] = data.get("value")
        return result

    def get(self, key: str, default: Any = None) -> Any:
        return self.get_preference(key, default)

    def set(self, key: str, value: Any) -> None:
        self.set_preference(key, value)

    def delete(self, key: str) -> None:
        """Delete a preference."""
        self._cache.pop(key, None)
        path = self._get_path(key)
        if path.exists():
            path.unlink()

    def clear(self) -> None:
        """Clear all preferences."""
        self._cache.clear()
        for f in self._prefs_dir.glob("*.json"):
            f.unlink()

    def to_context_string(self, max_tokens: int = 1000) -> str:
        """Serialize preferences to context string."""
        if not self._cache:
            return ""
        budget_chars = max_tokens * 4
        parts = []
        current_len = 0
        for key, data in self._cache.items():
            value = data.get("value", "")
            entry = f"{key}: {value}"
            if current_len + len(entry) + 2 <= budget_chars:
                parts.append(entry)
                current_len += len(entry) + 2
            else:
                break
        return "\n".join(parts)

    @property
    def memory_type(self) -> str:
        return "preference"
