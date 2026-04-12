"""
状态机单元测试
"""

import pytest
from domain.entities.state_machine import StateMachine, AgentState


class TestStateMachine:
    """测试状态机"""

    def test_initial_state(self):
        """测试初始状态"""
        sm = StateMachine()
        assert sm.get_current_state() == AgentState.INITIAL

    def test_valid_transition(self):
        """测试有效状态转换"""
        sm = StateMachine()
        sm.transition(AgentState.REQUIREMENT_GATHERING, "Start gathering requirements")
        assert sm.get_current_state() == AgentState.REQUIREMENT_GATHERING

    def test_invalid_transition(self):
        """测试无效状态转换"""
        sm = StateMachine()
        # 从 INITIAL 不能直接到 PLANNING
        with pytest.raises(ValueError, match="Invalid state transition"):
            sm.transition(AgentState.PLANNING, "Try to plan directly")

    def test_state_history(self):
        """测试状态历史"""
        sm = StateMachine()
        sm.transition(AgentState.REQUIREMENT_GATHERING, "Start gathering")
        sm.transition(AgentState.REQUIREMENT_CONFIRMED, "Requirements confirmed")

        history = sm.transitions
        assert len(history) >= 2

    def test_requirements_confirmed(self):
        """测试需求确认状态"""
        sm = StateMachine()
        sm.transition(AgentState.REQUIREMENT_GATHERING, "Start gathering")
        sm.transition(AgentState.REQUIREMENT_CONFIRMED, "Requirements confirmed")

        # 检查当前状态是否是 REQUIREMENT_CONFIRMED
        assert sm.get_current_state() == AgentState.REQUIREMENT_CONFIRMED


class TestAgentState:
    """测试 AgentState 枚举"""

    def test_state_values(self):
        """测试状态值"""
        assert AgentState.INITIAL.value == "initial"
        assert AgentState.REQUIREMENT_GATHERING.value == "gathering"
        assert AgentState.REQUIREMENT_CONFIRMED.value == "confirmed"
        assert AgentState.PLANNING.value == "planning"
        assert AgentState.EXECUTING.value == "executing"
        assert AgentState.STAGE_COMPLETED.value == "stage_completed"
        assert AgentState.TASK_COMPLETED.value == "task_completed"
        assert AgentState.ERROR.value == "error"
