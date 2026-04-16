"""极简配置管理"""

import toml
from pathlib import Path
from typing import Any, Dict, Optional

_global_config: Optional[Dict[str, Any]] = None


def get_config() -> Dict[str, Any]:
    """获取配置"""
    global _global_config
    if _global_config is None:
        config_file = Path("nanoagent.toml")
        if config_file.exists():
            _global_config = toml.loads(config_file.read_text())
        else:
            _global_config = _get_default_config()
    return _global_config


def _get_default_config() -> Dict[str, Any]:
    """默认配置"""
    return {
        "llm": {
            "model": "openai/gpt-4o",
            "temperature": 0.7,
            "max_tokens": 4096,
            "mock": {
                "enabled": True,
                "mode": "random",
                "responses_file": "tests/fixtures/llm_mock_simple.json",
            },
        }
    }
