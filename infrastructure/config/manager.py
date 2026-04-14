"""配置管理器"""

import os
import toml
from pathlib import Path
from typing import Dict, Any
from loguru import logger

_global_config = None


class ConfigManager:
    def __init__(self, config_dir: str = "config", main_config: str = "nanoagent.toml"):
        self.config_dir = Path(config_dir)
        self.main_config = self._load_toml(Path(main_config))
        self.module_configs = {}

        for name, path in self.main_config.get("modules", {}).items():
            try:
                self.module_configs[name] = self._load_toml(Path(path))
            except Exception as e:
                logger.warning(f"Failed to load config {name}: {e}")
                self.module_configs[name] = {}

    def _load_toml(self, path: Path) -> Dict[str, Any]:
        if path.exists():
            with open(path) as f:
                return toml.load(f)
        return {}

    def get_module_config(self, module: str) -> Dict[str, Any]:
        return self.module_configs.get(module, {})

    def get_path(self, key: str, default: str = "") -> str:
        """获取路径配置"""
        paths = self.main_config.get("paths", {})
        return paths.get(key, default)


def get_config_manager() -> ConfigManager:
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config
