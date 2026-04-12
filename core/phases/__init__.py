"""
执行阶段模块

将 ReAct 循环的各个阶段拆分为独立的处理器类
"""

from .thinking import ThinkingPhase
from .acting import ActingPhase
from .observing import ObservingPhase
from .reflection import ReflectionPhase
from .planning import PlanningPhase

__all__ = [
    "ThinkingPhase",
    "ActingPhase",
    "ObservingPhase",
    "ReflectionPhase",
    "PlanningPhase",
]
