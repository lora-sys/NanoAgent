"""
表现层 - 用户界面

包含：
- CLI 界面 (cli/)
"""

from .cli.interface import CLIInterface, get_cli

__all__ = ["CLIInterface", "get_cli"]
