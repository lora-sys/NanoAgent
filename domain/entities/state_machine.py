"""Deterministic state machine for agent lifecycle management."""

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from loguru import logger


class AgentState(Enum):
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
    from_state: AgentState
    to_state: AgentState
    reason: str
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)


class StateMachine:
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
            AgentState.EXECUTING,
            AgentState.ERROR,
        ],
        AgentState.STAGE_COMPLETED: [
            AgentState.PLANNING,
            AgentState.TASK_COMPLETED,
            AgentState.ERROR,
        ],
        AgentState.TASK_COMPLETED: [AgentState.INITIAL],
        AgentState.ERROR: [AgentState.INITIAL, AgentState.EXECUTING],
    }

    def __init__(self):
        self.current_state = AgentState.INITIAL
        self.transitions: List[StateTransition] = []
        logger.info("StateMachine initialized with initial state")

    def can_transition(self, new_state: AgentState) -> bool:
        return new_state in self.TRANSITIONS.get(self.current_state, [])

    def transition(
        self, new_state: AgentState, reason: str, metadata: Optional[Dict] = None
    ):
        if not self.can_transition(new_state):
            error_msg = f"Invalid state transition: {self.current_state.value} -> {new_state.value}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        old_state = self.current_state
        self.current_state = new_state
        self.transitions.append(
            StateTransition(
                old_state, new_state, reason, datetime.now(), metadata or {}
            )
        )
        logger.info(f"State transition: {old_state.value} -> {new_state.value}")

    def get_current_state(self) -> AgentState:
        return self.current_state

    def get_transition_history(self) -> List[StateTransition]:
        return self.transitions.copy()

    def get_transition_history_dict(self) -> List[Dict]:
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
        logger.info("Resetting StateMachine")
        self.current_state = AgentState.INITIAL
        self.transitions.clear()

    def __repr__(self) -> str:
        return f"StateMachine(current_state={self.current_state.value}, transitions={len(self.transitions)})"
