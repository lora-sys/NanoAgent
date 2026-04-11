"""
状态机模块 - NanoAgent
提供确定性的状态管理和转换机制
"""

from enum import Enum
from typing import Dict, List
from datetime import datetime
from dataclasses import dataclass, field
from loguru import logger


class AgentState(Enum):
    """Agent 执行状态"""

    INITIAL = "initial"  # 初始状态
    REQUIREMENT_GATHERING = "gathering"  # 需求收集中
    REQUIREMENT_CONFIRMED = "confirmed"  # 需求已确认
    PLANNING = "planning"  # 规划中
    EXECUTING = "executing"  # 执行中
    STAGE_COMPLETED = "stage_completed"  # 阶段完成
    TASK_COMPLETED = "task_completed"  # 任务完成
    ERROR = "error"  # 错误状态


@dataclass
class StateTransition:
    """状态转换记录"""

    from_state: AgentState
    to_state: AgentState
    reason: str
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)


class StateMachine:
    """确定性状态机"""

    # 状态转换规则
    TRANSITIONS = {
        AgentState.INITIAL: [AgentState.REQUIREMENT_GATHERING, AgentState.ERROR],
        AgentState.REQUIREMENT_GATHERING: [
            AgentState.REQUIREMENT_CONFIRMED,
            AgentState.ERROR,
        ],
        AgentState.REQUIREMENT_CONFIRMED: [AgentState.PLANNING, AgentState.ERROR],
        AgentState.PLANNING: [AgentState.EXECUTING, AgentState.ERROR],
        AgentState.EXECUTING: [
            AgentState.STAGE_COMPLETED,
            AgentState.EXECUTING,  # 继续执行
            AgentState.ERROR,
        ],
        AgentState.STAGE_COMPLETED: [
            AgentState.PLANNING,  # 下一阶段规划
            AgentState.TASK_COMPLETED,
            AgentState.ERROR,
        ],
        AgentState.TASK_COMPLETED: [
            AgentState.INITIAL  # 可以开始新任务
        ],
        AgentState.ERROR: [
            AgentState.INITIAL,
            AgentState.EXECUTING,  # 重试
        ],
    }

    def __init__(self):
        self.current_state = AgentState.INITIAL
        self.transitions: List[StateTransition] = []
        logger.info("StateMachine initialized with initial state")

    def can_transition(self, new_state: AgentState) -> bool:
        """检查是否可以转换到新状态"""
        return new_state in self.TRANSITIONS.get(self.current_state, [])

    def transition(self, new_state: AgentState, reason: str, metadata: Dict = None):
        """执行状态转换"""
        # 验证转换合法性
        if not self.can_transition(new_state):
            old_state_name = self.current_state.value
            new_state_name = new_state.value
            error_msg = (
                f"Invalid state transition: {old_state_name} -> {new_state_name}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 执行转换
        old_state = self.current_state
        self.current_state = new_state

        # 记录转换
        transition = StateTransition(
            from_state=old_state,
            to_state=new_state,
            reason=reason,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )
        self.transitions.append(transition)

        logger.info(
            f"State transition: {old_state.value} -> {new_state.value}",
            reason=reason,
            metadata=metadata,
        )

    def get_current_state(self) -> AgentState:
        """获取当前状态"""
        return self.current_state

    def get_transition_history(self) -> List[StateTransition]:
        """获取转换历史"""
        return self.transitions.copy()

    def get_transition_history_dict(self) -> List[Dict]:
        """获取转换历史（字典格式）"""
        return [
            {
                "from_state": t.from_state.value,
                "to_state": t.to_state.value,
                "reason": t.reason,
                "timestamp": t.timestamp.isoformat(),
                "metadata": t.metadata,
            }
            for t in self.transitions
        ]

    def reset(self):
        """重置状态机"""
        logger.info("Resetting StateMachine")
        self.current_state = AgentState.INITIAL
        self.transitions.clear()

    def __repr__(self) -> str:
        return f"StateMachine(current_state={self.current_state.value}, transitions={len(self.transitions)})"


# 导出
__all__ = ["AgentState", "StateTransition", "StateMachine"]
