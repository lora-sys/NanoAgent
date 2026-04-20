"""lifecycle 单元测试"""

import pytest

from core.lifecycle import (
    Lifecycle,
    EventType,
    event_to_dict,
    AgentStartEvent,
    AgentEndEvent,
    TurnStartEvent,
    TurnEndEvent,
    MessageStartEvent,
    MessageEndEvent,
    ToolStartEvent,
    ToolEndEvent,
    TurnContext,
)


@pytest.mark.unit
class TestLifecycle:
    """Lifecycle 核心功能测试"""

    def test_balanced_sequence(self):
        """平衡序列: agent > turn > message/tool"""
        lc = Lifecycle()
        lc.emit(AgentStartEvent(task="test"))
        assert lc._depth == 1
        lc.emit(TurnStartEvent(turn_context=TurnContext(1, 1)))
        assert lc._depth == 2
        lc.emit(MessageStartEvent(turn_number=1))
        assert lc._depth == 3
        lc.emit(MessageEndEvent(turn_number=1, content="hi", tool_calls=[]))
        assert lc._depth == 2
        lc.emit(ToolStartEvent(turn_number=1, tool_call_id="tc_0", tool_name="grep", args={}))
        assert lc._depth == 3
        lc.emit(ToolEndEvent(turn_number=1, tool_call_id="tc_0", tool_name="grep", result={}, is_error=False))
        assert lc._depth == 2
        lc.emit(TurnEndEvent(turn_context=TurnContext(1, 1)))
        assert lc._depth == 1
        lc.emit(AgentEndEvent(status="completed", total_turns=1, total_tools=1))
        assert lc._depth == 0

    def test_multiple_turns(self):
        """多轮对话"""
        lc = Lifecycle()
        lc.emit(AgentStartEvent(task="test"))
        for i in range(3):
            lc.emit(TurnStartEvent(turn_context=TurnContext(i + 1, i + 1)))
            lc.emit(MessageStartEvent(turn_number=i + 1))
            lc.emit(MessageEndEvent(turn_number=i + 1, content="", tool_calls=[]))
            lc.emit(TurnEndEvent(turn_context=TurnContext(i + 1, i + 1)))
        lc.emit(AgentEndEvent(status="completed", total_turns=3, total_tools=0))
        assert lc._depth == 0

    def test_multiple_tools_per_turn(self):
        """单轮多工具调用"""
        lc = Lifecycle()
        lc.emit(AgentStartEvent(task="test"))
        lc.emit(TurnStartEvent(turn_context=TurnContext(1, 1)))
        lc.emit(MessageStartEvent(turn_number=1))
        lc.emit(MessageEndEvent(turn_number=1, content="", tool_calls=[("grep", {}), ("read_file", {})]))
        for i, name in enumerate(["grep", "read_file"]):
            lc.emit(ToolStartEvent(turn_number=1, tool_call_id=f"tc_{i}", tool_name=name, args={}))
            lc.emit(ToolEndEvent(turn_number=1, tool_call_id=f"tc_{i}", tool_name=name, result={}, is_error=False))
        lc.emit(TurnEndEvent(turn_context=TurnContext(1, 1)))
        lc.emit(AgentEndEvent(status="completed", total_turns=1, total_tools=2))
        assert lc._depth == 0
        assert lc.get_totals() == (1, 2)

    def test_wrong_depth_raises(self):
        """错误嵌套层级抛出 RuntimeError"""
        lc = Lifecycle()
        with pytest.raises(RuntimeError, match="AGENT_END.*depth 0.*expected 1"):
            lc.emit(AgentEndEvent(status="completed"))

    def test_wrong_turn_depth_raises(self):
        """Turn 在错误层级抛出"""
        lc = Lifecycle()
        lc.emit(AgentStartEvent(task="test"))
        with pytest.raises(RuntimeError, match="TURN_END.*depth 1.*expected 2"):
            lc.emit(TurnEndEvent(turn_context=TurnContext(1, 1)))

    def test_subscribe_unsubscribe(self):
        """handler 注册和注销"""
        lc = Lifecycle()
        received = []

        def handler(e):
            received.append(e.type.name)

        lc.subscribe(handler)
        lc.emit(AgentStartEvent(task="test"))
        assert "AGENT_START" in received

        lc.unsubscribe(handler)
        received.clear()
        lc.emit(AgentEndEvent(status="completed", total_turns=0, total_tools=0))
        assert len(received) == 0

    def test_multiple_handlers(self):
        """多个 handler 同时接收"""
        lc = Lifecycle()
        counts = [0, 0]

        def make_handler(idx):
            def h(e):
                counts[idx] += 1
            return h

        lc.subscribe(make_handler(0))
        lc.subscribe(make_handler(1))
        lc.emit(AgentStartEvent(task="test"))
        assert counts == [1, 1]

    def test_totals_tracking(self):
        """total_turns 和 total_tools 统计"""
        lc = Lifecycle()
        assert lc.get_totals() == (0, 0)

        lc.emit(AgentStartEvent(task="test"))
        lc.emit(TurnStartEvent(turn_context=TurnContext(1, 1)))
        assert lc.get_totals() == (1, 0)

        lc.emit(MessageStartEvent(turn_number=1))
        lc.emit(MessageEndEvent(turn_number=1, content="", tool_calls=[]))
        lc.emit(ToolStartEvent(turn_number=1, tool_call_id="tc_0", tool_name="grep", args={}))
        lc.emit(ToolEndEvent(turn_number=1, tool_call_id="tc_0", tool_name="grep", result={}, is_error=False))
        assert lc.get_totals() == (1, 1)

        lc.emit(TurnEndEvent(turn_context=TurnContext(1, 1)))
        assert lc.get_totals() == (1, 1)

    def test_turn_number(self):
        """turn_number 递增"""
        lc = Lifecycle()
        lc.emit(AgentStartEvent(task="test"))
        assert lc.get_turn_number() == 0

        lc.emit(TurnStartEvent(turn_context=TurnContext(1, 1)))
        assert lc.get_turn_number() == 1

        lc.emit(TurnEndEvent(turn_context=TurnContext(1, 1)))
        assert lc.get_turn_number() == 1

        lc.emit(TurnStartEvent(turn_context=TurnContext(2, 2)))
        assert lc.get_turn_number() == 2

    def test_event_to_dict(self):
        """event_to_dict 转换"""
        e = AgentStartEvent(task="read README")
        d = event_to_dict(e)
        assert d["type"] == "AGENT_START"
        assert d["task"] == "read README"

        e2 = ToolEndEvent(
            turn_number=1, tool_call_id="tc_0", tool_name="grep", result={}, is_error=False
        )
        d2 = event_to_dict(e2)
        assert d2["type"] == "TOOL_EXECUTION_END"
        assert d2["tool_name"] == "grep"
        assert d2["is_error"] is False

    def test_Tracer_integration(self):
        """Tracer 作为 lifecycle handler"""
        pytest.importorskip("core.observability")
        from core.observability import get_tracer
        from core.lifecycle import AgentStartEvent, AgentEndEvent

        tracer = get_tracer()
        lc = Lifecycle()
        lc.subscribe(tracer)

        lc.emit(AgentStartEvent(task="test session"))
        assert tracer.get_current_session() is not None
        assert tracer.get_current_session().task == "test session"

        lc.emit(AgentEndEvent(status="ok", total_turns=2, total_tools=3))
        assert tracer.get_current_session() is None
