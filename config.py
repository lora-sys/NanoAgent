"""配置管理"""

import toml
from pathlib import Path
from typing import Any, Dict, Optional

from exceptions import ConfigError

_global_config: Optional["Config"] = None


class Config:
    def __init__(self, config_file: str = "nanoagent.toml"):
        self._config_file = Path(config_file)
        self._main: Dict[str, Any] = {}
        self._modules: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if not self._config_file.exists():
            raise ConfigError(f"Config file not found: {self._config_file}")
        self._main = toml.loads(self._config_file.read_text())
        modules = self._main.get("modules", {})
        config_dir = self._config_file.parent / self._main.get("general", {}).get("config_dir", "config")
        for name, rel_path in modules.items():
            module_file = config_dir / rel_path
            self._modules[name] = toml.loads(module_file.read_text()) if module_file.exists() else {}

    def get(self, module: str, key: str, default: Any = None) -> Any:
        mod = self._modules.get(module, {})
        value = mod
        for k in key.split("."):
            value = value.get(k) if isinstance(value, dict) else default
        return value if value is not None else default

    def get_module(self, module: str) -> Dict[str, Any]:
        return self._modules.get(module, {})


def get_config() -> Config:
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config
