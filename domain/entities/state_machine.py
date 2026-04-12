"""
状态机模块 - NanoAgent
提供确定性的状态管理和转换机制。

该模块定义了 Agent 的生命周期状态（如初始、需求收集、执行中等）
以及状态之间的合法转换规则。它确保了 Agent 执行流程的有序性和可追溯性。
"""

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from loguru import logger


class AgentState(Enum):
    """Agent 执行状态枚举。

    定义了 Agent 在生命周期中可能处于的所有状态。

    Attributes:
        INITIAL: 初始状态，任务刚开始。
        REQUIREMENT_GATHERING: 需求收集中，正在询问用户以明确需求。
        REQUIREMENT_CONFIRMED: 需求已确认，用户已认可当前需求。
        PLANNING: 规划中，正在制定执行计划。
        EXECUTING: 执行中，正在按计划执行任务。
        STAGE_COMPLETED: 阶段完成，当前阶段任务已完成。
        TASK_COMPLETED: 任务完成，整个任务已全部完成。
        ERROR: 错误状态，执行过程中发生了不可恢复的错误。
    """

    INITIAL = "initial"
    REQUIREMENT_GATHERING = "gathering"
    REQUIREMENT_CONFIRMED = "confirmed"
    PLANNING = "planning"
    EXECUTING = "executing"
    STAGE_COMPLETED = "stage_completed"
    TASK_COMPLETED = "task_completed"
    ERROR = "error"


@dataclass
class StateTransition:
    """状态转换记录数据类。

    用于记录每一次状态变更的详细信息，以便审计和调试。

    Attributes:
        from_state: 转换前的状态。
        to_state: 转换后的状态。
        reason: 导致转换的原因描述。
        timestamp: 转换发生的时间戳。
        metadata: 附加的元数据字典。
    """

    from_state: AgentState
    to_state: AgentState
    reason: str
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)


class StateMachine:
    """确定性状态机。

    管理 Agent 的状态转换，确保所有的状态流转都遵循预定义的规则（TRANSITIONS）。
    任何非法的状态跳转都会被阻止并抛出异常。

    Attributes:
        current_state: 当前所处的状态。
        transitions: 历史状态转换记录列表。

    Example:
        >>> sm = StateMachine()
        >>> sm.transition(AgentState.REQUIREMENT_GATHERING, "用户发起任务")
    """

    # 状态转换规则映射：当前状态 -> [允许的下一状态列表]
    TRANSITIONS: Dict[AgentState, List[AgentState]] = {
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
        """初始化状态机。

        将初始状态设置为 `AgentState.INITIAL`。
        """
        self.current_state = AgentState.INITIAL
        self.transitions: List[StateTransition] = []
        logger.info("StateMachine initialized with initial state")

    def can_transition(self, new_state: AgentState) -> bool:
        """检查是否可以转换到目标状态。

        Args:
            new_state: 目标状态。

        Returns:
            如果转换合法返回 True，否则返回 False。
        """
        return new_state in self.TRANSITIONS.get(self.current_state, [])

    def transition(
        self, new_state: AgentState, reason: str, metadata: Optional[Dict] = None
    ):
        """执行状态转换。

        验证转换的合法性，如果合法则更新状态并记录日志。
        如果不合法，将抛出 `ValueError` 异常。

        Args:
            new_state: 目标状态。
            reason: 转换原因的文本描述。
            metadata: 附加的元数据字典。

        Raises:
            ValueError: 当尝试进行非法状态转换时抛出。

        Example:
            >>> sm.transition(AgentState.REQUIREMENT_GATHERING, "用户输入了任务描述")
        """
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
        """获取当前状态。

        Returns:
            当前的 AgentState 枚举值。
        """
        return self.current_state

    def get_transition_history(self) -> List[StateTransition]:
        """获取状态转换历史记录。

        Returns:
            StateTransition 对象列表的副本。
        """
        return self.transitions.copy()

    def get_transition_history_dict(self) -> List[Dict]:
        """获取状态转换历史记录（字典格式）。

        Returns:
            包含转换历史的字典列表。
        """
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
        """重置状态机。

        将状态重置为 INITIAL 并清空转换历史。
        """
        logger.info("Resetting StateMachine")
        self.current_state = AgentState.INITIAL
        self.transitions.clear()

    def __repr__(self) -> str:
        """返回状态机的字符串表示。"""
        return f"StateMachine(current_state={self.current_state.value}, transitions={len(self.transitions)})"


# 导出
__all__ = ["AgentState", "StateTransition", "StateMachine"]
