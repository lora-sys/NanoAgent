"""Core modules - lazy imports to avoid circular dependency.

Import individual modules directly when needed:
    from core.agent import NanoAgent
    from core.chain import PromptChain
    etc.
"""

from core.spec import TaskSpec
from core.context import ExecutionContext, ChainContext, RouteContext
from core.utils import extract_json

__all__ = [
    "TaskSpec",
    "ExecutionContext",
    "ChainContext",
    "RouteContext",
    "extract_json",
]
